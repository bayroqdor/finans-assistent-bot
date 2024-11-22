# db_functions.py

import sqlite3
from datetime import datetime
from utilities import sanitize_comment

def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    # Create tables
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        language TEXT,
                        first_time BOOLEAN DEFAULT 1,
                        family_id INTEGER,
                        role TEXT,
                        budget REAL DEFAULT 0
                    )'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS incomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        date TIMESTAMP,
                        amount REAL,
                        currency TEXT,
                        category TEXT,
                        comment TEXT,
                        family_id INTEGER,
                        approved BOOLEAN DEFAULT 1,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        date TIMESTAMP,
                        amount REAL,
                        currency TEXT,
                        category TEXT,
                        comment TEXT,
                        family_id INTEGER,
                        approved BOOLEAN DEFAULT 1,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS families (
                        family_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        family_name TEXT,
                        head_id INTEGER
                    )'''
    )
    conn.commit()
    conn.close()
    # Ensure columns exist
    add_column_if_not_exists('users', 'family_id', 'INTEGER')
    add_column_if_not_exists('users', 'role', 'TEXT')
    add_column_if_not_exists('users', 'budget', 'REAL DEFAULT 0')
    add_column_if_not_exists('incomes', 'family_id', 'INTEGER')
    add_column_if_not_exists('expenses', 'family_id', 'INTEGER')
    add_column_if_not_exists('incomes', 'approved', 'BOOLEAN DEFAULT 1')
    add_column_if_not_exists('expenses', 'approved', 'BOOLEAN DEFAULT 1')


def add_column_if_not_exists(table_name, column_name, column_definition):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    # Check if column exists
    c.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in c.fetchall()]
    if column_name not in columns:
        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
    conn.commit()
    conn.close()


def get_user_language(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def set_user_language(user_id, language):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result:
        # User exists, update language and set first_time to False
        c.execute(
            'UPDATE users SET language = ?, first_time = 0 WHERE user_id = ?', (language, user_id)
        )
    else:
        # New user, insert record with first_time = 1
        c.execute(
            'INSERT INTO users (user_id, language, first_time) VALUES (?, ?, 1)',
            (user_id, language),
        )
    conn.commit()
    conn.close()


def is_first_time_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT first_time FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return bool(result[0])
    else:
        return True  # Default to True if user not found


def get_user_role(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def get_user_family_id(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT family_id FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def create_family(family_name, head_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('INSERT INTO families (family_name, head_id) VALUES (?, ?)', (family_name, head_id))
    family_id = c.lastrowid
    # Update user's family_id and role
    c.execute('UPDATE users SET family_id = ?, role = ? WHERE user_id = ?', (family_id, 'head', head_id))
    conn.commit()
    conn.close()
    return family_id


def join_family(user_id, family_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('UPDATE users SET family_id = ?, role = ? WHERE user_id = ?', (family_id, 'member', user_id))
    conn.commit()
    conn.close()


def save_income(user_id, user_data):
    from family_budget import notify_family_head
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    current_time = datetime.now()
    # Sanitize comment input
    comment = sanitize_comment(user_data['income_comment'])
    family_id = get_user_family_id(user_id)
    approved = 1
    role = get_user_role(user_id)
    if role == 'member' and family_id is not None:
        approved = 0  # Needs approval from head
    c.execute(
        'INSERT INTO incomes (user_id, date, amount, currency, category, comment, family_id, approved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            user_id,
            current_time,
            user_data['income_amount'],
            user_data['income_currency'],
            user_data['income_category'],
            comment,
            family_id,
            approved,
        ),
    )
    income_id = c.lastrowid
    conn.commit()
    conn.close()
    if approved == 0:
        # Notify family head for approval
        notify_family_head(family_id, income_id, 'income', user_id)


def save_expense(user_id, user_data):
    from family_budget import notify_family_head
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    current_time = datetime.now()
    # Sanitize comment input
    comment = sanitize_comment(user_data['expense_comment'])
    family_id = get_user_family_id(user_id)
    approved = 1
    role = get_user_role(user_id)
    if role == 'member' and family_id is not None:
        approved = 0  # Needs approval from head
    c.execute(
        'INSERT INTO expenses (user_id, date, amount, currency, category, comment, family_id, approved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            user_id,
            current_time,
            user_data['expense_amount'],
            user_data['expense_currency'],
            user_data['expense_category'],
            comment,
            family_id,
            approved,
        ),
    )
    expense_id = c.lastrowid
    conn.commit()
    conn.close()
    if approved == 0:
        # Notify family head for approval
        notify_family_head(family_id, expense_id, 'expense', user_id)


def approve_transaction(transaction_id, transaction_type):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    if transaction_type == 'income':
        c.execute('UPDATE incomes SET approved = 1 WHERE id = ?', (transaction_id,))
    elif transaction_type == 'expense':
        c.execute('UPDATE expenses SET approved = 1 WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()


def reject_transaction(transaction_id, transaction_type):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    if transaction_type == 'income':
        c.execute('DELETE FROM incomes WHERE id = ?', (transaction_id,))
    elif transaction_type == 'expense':
        c.execute('DELETE FROM expenses WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()


def get_family_head_id(family_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT head_id FROM families WHERE family_id = ?', (family_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def get_user_budget(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT budget FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return 0


def set_user_budget(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('UPDATE users SET budget = ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()


def reduce_user_budget(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    current_budget = get_user_budget(user_id)
    new_budget = current_budget - amount
    c.execute('UPDATE users SET budget = ? WHERE user_id = ?', (new_budget, user_id))
    conn.commit()
    conn.close()
