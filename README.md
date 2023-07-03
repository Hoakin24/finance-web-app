# Finance: A Full-Stack Web App to Simulate Trading of Stocks

## Technologies Used

Finance utilizes the following technologies:

- Python: The programming language used to build the backend logic of the web application.
- Flask: A micro web framework in Python used for creating web routes and handling HTTP requests.
- Jinja: A templating engine that allows embedding Python code within HTML templates to generate dynamic web pages.
- Bootstrap: A popular CSS framework used for styling the web application, providing a responsive and visually appealing design.
- SQL: Structured Query Language is used for managing the database that stores user information, stock data, and transactions.

## Summary

Finance allows users to register, buy and sell stocks, and manage their stock portfolios. The application retrieves real-time stock prices from an API and uses a database to store user information and transaction history. It provides an interactive and user-friendly interface to simulate stock trading.

## How to Run

To run Finance, follow these steps:

1. Clone this repository to your local machine.
2. Navigate to the project directory using the command line.
3. Activate a virtual environment by running the command: `python3 -m venv .venv`.
4. Select the virtual environment as the active workspace.
5. Install the project dependencies by running the command: `pip install -r requirements.txt`.
6. Set the Flask environment variable by running the command: `export FLASK_APP=application.py`.
7. Configure and export your API key as per the provided instructions.
8. Run the command: `flask run` to start the application on your localhost.

## Content

The navigation bar of the Finance web application includes the following links:

- Register: Allows users to create a new account.
- Quote: Allows users to retrieve the current price and information for a specific stock.
- Buy: Enables users to buy stocks by specifying the symbol and quantity.
- Index: Takes users to the homepage, where they can see an overview of their portfolio and current stock prices.
- Sell: Allows users to sell stocks from their portfolio.
- History: Shows the transaction history for the user, including the date, stock, and quantity bought or sold.
- User: Provides a personalized touch by allowing users tprobo change their own password.
