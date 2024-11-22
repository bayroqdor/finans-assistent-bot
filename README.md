# Telegram Bot: Family Budget and Expense Tracker


## Introduction

This Telegram Bot is designed to help individuals and families manage their budgets by tracking incomes and expenses. It offers features such as graphical reports, family budget management, and multi-language support in Uzbek and Russian.
Features

Income and Expense Tracking: Users can record their incomes and expenses with details like amount, currency, category, and comments.
Graphical Reports: Generate weekly and monthly reports with graphical representations of income and expenses over time and category distributions.
Family Budget Management:
        Family Registration: Users can create a family group to manage a shared budget.
        Joining Families: Users can join existing family groups.
        Expense Approval: Family heads can approve or reject expenses submitted by family members.
        Budget Allocation: Allocate budgets to family members and monitor their spending.
    Multi-language Support: The bot supports Uzbek and Russian languages.
    User-friendly Interface: Interactive menus and prompts guide users through various functionalities.

Project Structure

The project is modularized into several Python files for better maintainability:

    main.py: The entry point of the bot. It initializes the bot and registers all the handlers.
    db_functions.py: Contains functions for interacting with the SQLite database.
    handlers.py: Houses all the command and message handlers that manage the bot's conversation flow.
    utilities.py: Includes utility functions like message deletion and input sanitization.
    report_generation.py: Handles the creation of text and graphical reports.
    family_budget.py: Contains functions related to family budget management, such as creating families and approving expenses.
    language_data.py: Stores all language-specific texts and translations.
    constants.py: Defines constants and state variables used throughout the bot.
    bot_database.db: SQLite database file where all user data, transactions, and family information are stored.

### Installation

To set up the bot on your local machine or server, follow these steps:

Clone the Repository:

    git clone https://github.com/bayroqdor/finans-assistent-bot.git
    cd finans-assistent-bot

Create a Virtual Environment (Optional but Recommended):

    python3 -m venv venv
    source venv/bin/activate  # On Windows, use venv\Scripts\activate

Install Dependencies:

    pip install -r requirements.txt

The requirements.txt should include:

    python-telegram-bot
    matplotlib
    pandas
    openpyxl

#### Set Up the Bot Token:

    Obtain a bot token from BotFather on Telegram.
    Replace 'YOUR_TELEGRAM_BOT_TOKEN_HERE' with your actual bot token in the constants.py file.

#### Configuration

No additional configuration is required. The bot uses an SQLite database (bot_database.db) that will be created automatically when the bot runs for the first time.
Running the Bot

#### Start the bot by running:

    python main.py

Ensure that your system meets all the dependencies and that the bot token is correctly set.
Usage
Start Command

    Command: /start
    Description: Initializes the bot and prompts the user to select a language if they are a new user.

#### Main Menu Options

After the /start command, users are presented with a main menu that includes:

    Income (⬇️Kirim / ⬇️Доход)
    Expense (⬆️Chiqim / ⬆️Расход)
    Report (🔄Hisobot / 🔄Отчет)
    Family Budget (👨‍👩‍👧‍👦 Oila budjeti / 👨‍👩‍👧‍👦 Семейный бюджет)
    Settings (⚙️Parametr / ⚙️Параметр)

#### Income Entry

    Process:
        Prompt for the income amount.
        Select the currency (e.g., USD, UZS).
        Choose a category (e.g., Salary, Gift).
        Enter an optional comment.
    Notes:
        Input validations ensure that the amount is a valid number.
        If the user is a family member, the income entry may require approval from the family head.

#### Expense Entry

    Process:
        Prompt for the expense amount.
        Select the currency.
        Choose a category (e.g., Food, Transport).
        Enter an optional comment.
    Notes:
        Family members' expenses may require approval.
        Budget checks are performed if budgets are allocated.

#### Reports

    Options:
        Weekly Report: Shows data from the past 7 days.
        Monthly Report: Shows data from the past 30 days.
        Graphical Reports:
            Income and Expense Over Time: Bar charts showing trends over months.
            Category Distribution: Pie charts showing expense distribution across categories.
    Actions:
        View reports directly in Telegram.
        Download reports as Excel files.

#### Family Budget Management

    For Family Heads:
        Create Family: Register a new family group.
        Set Budgets: Allocate budgets to family members.
        Approve/Reject Expenses: Review expenses submitted by family members.
    For Family Members:
        Join Family: Request to join an existing family group.
        View Budget: Check allocated budget and spending.
    Process to Create a Family:
        Select "Register Family".
        Enter a family name.
        Receive a family ID for members to join.
    Process to Join a Family:
        Select "Join Family".
        Enter the family ID.
        Await approval from the family head.

#### Settings

    Change Language: Users can switch between Uzbek and Russian.
    Cancel Operation: Users can cancel any ongoing operation.

#### Database Schema

The bot uses an SQLite database with the following tables:

    Users:
        user_id (Primary Key)
        language
        first_time
        family_id
        role (e.g., 'head', 'member')
        budget
    Incomes:
        id (Primary Key)
        user_id (Foreign Key)
        date
        amount
        currency
        category
        comment
        family_id
        approved
    Expenses:
        Similar structure to the Incomes table.
    Families:
        family_id (Primary Key)
        family_name
        head_id

#### Localization

The bot supports Uzbek and Russian languages. All prompts, messages, and menu options are available in both languages. Language selection is made during the initial /start command and can be changed in the settings.
Dependencies

    Python 3.6 or higher
    python-telegram-bot: For interacting with the Telegram Bot API.
    matplotlib: For generating graphical reports.
    pandas: For data manipulation and analysis.
    openpyxl: For creating Excel reports.
    sqlite3: Built-in Python library for database management.

Install all dependencies using:

    pip install -r requirements.txt

### Contributing

Contributions are welcome! To contribute:

    Fork the repository.
    Create a new branch for your feature or bugfix.
    Commit your changes with clear messages.
    Open a pull request describing your changes.

Please ensure that your code adheres to the project's coding standards and passes all tests.
License

This project is licensed under the MIT License.
Contact

For any inquiries or support, please contact:

    Email: muhsinbek@umft.uz
    Telegram: @sysadminutes