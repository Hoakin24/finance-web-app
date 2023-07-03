import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

import sys

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get data manipulated by the user through buying and selling
    stockInfo = db.execute(
        "SELECT symbol, stock, SUM(shares) AS SHARES, price, SUM(total) AS TOTAL FROM stocks WHERE id = ? GROUP BY symbol",
        session["user_id"])

    # Get the cash of user
    leftCash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

    # Get the total amount the user has spent
    totalBought = db.execute("SELECT SUM(total) FROM stocks WHERE id = ?", session["user_id"])

    # Sets the money and renders the html
    try:
        allMoney = float(leftCash[0]["cash"]) + float(totalBought[0]["SUM(total)"])
        return render_template("index.html", stocks=stockInfo, cash=usd(leftCash[0]["cash"]), totalMoney=usd(allMoney))
    except TypeError:
        allMoney = 10000.00
        return render_template("index.html", stocks=stockInfo, cash=usd(leftCash[0]["cash"]), totalMoney=usd(allMoney))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST
    if request.method == "POST":

        # Put input of user in variables
        buySymbol = request.form.get("symbol")
        buyShares = request.form.get("shares")

        # Use the lookup() function
        buyLookedUp = lookup(buySymbol)

        # Check for user error
        if not buySymbol:
            return apology("missing symbol")
        elif buyLookedUp == None:
            return apology("invalid symbol")
        elif not buyShares:
            return apology("missing shares")
        elif not buyShares.isdigit():
            return apology("invalid shares")

        buyShares = int(buyShares)
        if buyShares <= 0:
            return apology("invalid shares")

        # Set important data to variables
        buyerId = db.execute("SELECT id FROM users WHERE id = ?", session["user_id"])
        buyStock = buyLookedUp["name"]
        buyPrice = buyLookedUp["price"]
        buyTime = datetime.now()

        # Calculate total money spent and set cash of user in a variable
        totalBuyPrice = buyShares * buyPrice
        cashOfBuyer = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        # Check if user can afford the stock
        if cashOfBuyer[0]["cash"] < totalBuyPrice:
            return apology("can't afford")
        else:
            remainingCash = int(cashOfBuyer[0]["cash"]) - totalBuyPrice

            # Update database
            db.execute("INSERT INTO stocks (id, stock, symbol, shares, price, total, time) VALUES(?, ?, ?, ?, ?, ?, ?)",
                       buyerId[0]["id"], buyStock, buySymbol, buyShares, buyPrice, totalBuyPrice, buyTime)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", remainingCash, buyerId[0]["id"])
            db.execute("UPDATE stocks SET symbol = UPPER(symbol)")

            flash("Bought!")

            return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Put history of user in a variable
    transactions = db.execute("SELECT symbol, shares, price, time FROM stocks WHERE id = ?", session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User has reached route via POST
    if request.method == "POST":
        symbolFromUser = request.form.get("symbol")
        lookedUp = lookup(symbolFromUser)

        # Check if stock exist
        if lookedUp == None:
            return apology("stock symbol does not exist")
        else:
            stock = lookedUp["name"]
            price = usd(lookedUp["price"])
            symbol = lookedUp["symbol"]
            return render_template("quoted.html", name=stock, price=price, symbol=symbol)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check for user error
        checkUsername = db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)
        if not username:
            return apology("missing username")
        elif not password:
            return apology("missing password")
        elif not confirmation:
            return apology("missing confirmation")
        elif checkUsername[0]["COUNT(*)"] == 1:
            return apology("username already exist")
        elif password != confirmation:
            return apology("passwords doesn't match")

        # Put new user inside the database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        # Log the user in after registering
        login = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = login[0]["id"]

        # try:
        #     db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))
        #     session["user_id"] = rows[0]["id"]
        # except:
        #     return apology("username already exist")

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User has reached route via POST
    if request.method == "POST":
        sellSymbol = request.form.get("symbol")
        sellShares = request.form.get("shares")

        sellLookedUp = lookup(sellSymbol)

        # Get number of shares user has
        shareAmount = db.execute("SELECT SUM(shares) FROM stocks WHERE id = ? AND symbol = ?", session["user_id"], sellSymbol)

        # Check for user error
        if not sellSymbol:
            return apology("missing symbol")
        elif sellLookedUp == None:
            return apology("invalid symbol")
        elif not sellShares:
            return apology("missing shares")
        elif not sellShares.isdigit():
            return apology("invalid shares")

        sellShares = int(sellShares)
        if sellShares <= 0 or sellShares > shareAmount[0]["SUM(shares)"]:
            return apology("invalid shares")

        # Set important data to variables
        sellerId = db.execute("SELECT id FROM users WHERE id = ?", session["user_id"])
        sellStock = sellLookedUp["name"]
        sellPrice = sellLookedUp["price"]
        totalSellPrice = sellShares * sellPrice
        sellShares = -abs(sellShares)
        sellTime = datetime.now()

        # Calculate the amount of money returned to user
        cashOfSeller = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        remainingCash = int(cashOfSeller[0]["cash"]) + totalSellPrice
        totalSellPrice = -abs(totalSellPrice)

        # Update database
        db.execute("INSERT INTO stocks (id, stock, symbol, shares, price, total, time) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   sellerId[0]["id"], sellStock, sellSymbol, sellShares, sellPrice, totalSellPrice, sellTime)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", remainingCash, sellerId[0]["id"])
        db.execute("UPDATE stocks SET symbol = UPPER(symbol)")

        flash("Sold!")

        return redirect("/")
    else:
        symbols = db.execute("SELECT SUM(shares) AS SHARES, symbol FROM stocks WHERE id = ? GROUP BY symbol", session["user_id"])
        return render_template("sell.html", symbols=symbols)


@app.route("/user", methods=["GET", "POST"])
@login_required
def user():
    """Change password of user"""

    # User has reached route via POST
    if request.method == "POST":

        # Prompt user for old and new password, and confirmation
        oldPassword = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        currentPassword = request.form.get("current_password")
        newPassword = request.form.get("new_password")
        newConfirmation = request.form.get("new_confirmation")

        # Check for user error
        if not currentPassword or not newPassword or not newConfirmation:
            return apology("missing fields")
        elif not check_password_hash(oldPassword[0]["hash"], currentPassword):
            return apology("invalid current password")
        elif newPassword != newConfirmation:
            return apology("passwords do not match")

        # Generate new password hash
        newPasswordHash = generate_password_hash(newPassword)

        # Update password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", newPasswordHash, session["user_id"])

        flash("Password Changed!")

        return redirect("/user")
    else:
        userName = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        return render_template("user.html", userName=userName[0]["username"])