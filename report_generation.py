# report_generation.py

import os
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3
from db_functions import get_user_family_id, get_user_language
from io import BytesIO
import logging



def create_report(user_id, period, language):
    conn = sqlite3.connect('bot_database.db')
    family_id = get_user_family_id(user_id)
    if family_id:
        # Get data for the family
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
    else:
        # Get data for the individual
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
    conn.close()

    if period == 'weekly':
        date_filter = datetime.now() - pd.Timedelta(days=7)
        if language == 'uz':
            file_name = 'Haftalik-hisobot.xlsx'
        else:
            file_name = 'Еженедельный-отчет.xlsx'
    elif period == 'monthly':
        date_filter = datetime.now() - pd.Timedelta(days=30)
        if language == 'uz':
            file_name = 'Oylik-hisobot.xlsx'
        else:
            file_name = 'Ежемесячный-отчет.xlsx'
    else:
        logging.error("Invalid period specified.")
        return None

    # Convert 'date' columns to datetime
    df_income['date'] = pd.to_datetime(df_income['date'])
    df_expense['date'] = pd.to_datetime(df_expense['date'])

    # Filter data based on date
    recent_income = df_income[df_income['date'] >= date_filter]
    recent_expense = df_expense[df_expense['date'] >= date_filter]

    if recent_income.empty and recent_expense.empty:
        # No data to generate report
        return None

    # Convert 'amount' column to numeric
    recent_income['amount'] = pd.to_numeric(recent_income['amount'], errors='coerce')
    recent_expense['amount'] = pd.to_numeric(recent_expense['amount'], errors='coerce')

    # Drop rows with NaN amounts
    recent_income = recent_income.dropna(subset=['amount'])
    recent_expense = recent_expense.dropna(subset=['amount'])

    # Remove 'id' and 'user_id' columns
    recent_income = recent_income.drop(columns=['id', 'user_id', 'family_id', 'approved'])
    recent_expense = recent_expense.drop(columns=['id', 'user_id', 'family_id', 'approved'])

    # Translate column names
    if language == 'uz':
        recent_income.rename(
            columns={
                'date': 'Sana',
                'amount': 'Summa',
                'currency': 'Valyuta',
                'category': 'Bo\'lim',
                'comment': 'Kommentariya',
            },
            inplace=True,
        )
        recent_expense.rename(
            columns={
                'date': 'Sana',
                'amount': 'Summa',
                'currency': 'Valyuta',
                'category': 'Bo\'lim',
                'comment': 'Kommentariya',
            },
            inplace=True,
        )
    else:
        recent_income.rename(
            columns={
                'date': 'Дата',
                'amount': 'Сумма',
                'currency': 'Валюта',
                'category': 'Категория',
                'comment': 'Комментарий',
            },
            inplace=True,
        )
        recent_expense.rename(
            columns={
                'date': 'Дата',
                'amount': 'Сумма',
                'currency': 'Валюта',
                'category': 'Категория',
                'comment': 'Комментарий',
            },
            inplace=True,
        )

    # Calculate total amounts by currency
    if language == 'uz':
        income_total = recent_income.groupby('Valyuta')['Summa'].sum().reset_index()
        expense_total = recent_expense.groupby('Valyuta')['Summa'].sum().reset_index()
    else:
        income_total = recent_income.groupby('Валюта')['Сумма'].sum().reset_index()
        expense_total = recent_expense.groupby('Валюта')['Сумма'].sum().reset_index()

    # Create total report dataframe
    if language == 'uz':
        total_df = pd.merge(
            income_total,
            expense_total,
            on='Valyuta',
            how='outer',
            suffixes=('_Kirim', '_Chiqim'),
        ).fillna(0)
        total_df['Balans'] = total_df['Summa_Kirim'] - total_df['Summa_Chiqim']
        # Rename columns
        total_df.rename(
            columns={
                'Valyuta': 'Valyuta',
                'Summa_Kirim': 'Umumiy Kirim',
                'Summa_Chiqim': 'Umumiy Chiqim',
                'Balans': 'Balans',
            },
            inplace=True,
        )
    else:
        total_df = pd.merge(
            income_total,
            expense_total,
            on='Валюта',
            how='outer',
            suffixes=('_Доход', '_Расход'),
        ).fillna(0)
        total_df['Баланс'] = total_df['Сумма_Доход'] - total_df['Сумма_Расход']
        # Rename columns
        total_df.rename(
            columns={
                'Валюта': 'Валюта',
                'Сумма_Доход': 'Общий Доход',
                'Сумма_Расход': 'Общий Расход',
                'Баланс': 'Баланс',
            },
            inplace=True,
        )

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        # Write total amounts
        if not total_df.empty:
            total_df.to_excel(
                writer, sheet_name='Umumiy Hisobot' if language == 'uz' else 'Общий Отчет', index=False
            )
        # Write detailed data
        if not recent_income.empty:
            recent_income.to_excel(
                writer, sheet_name='Kirimlar' if language == 'uz' else 'Доходы', index=False
            )
        if not recent_expense.empty:
            recent_expense.to_excel(
                writer, sheet_name='Chiqimlar' if language == 'uz' else 'Расходы', index=False
            )

    return file_name


def create_text_report(user_id, period, language):
    conn = sqlite3.connect('bot_database.db')
    family_id = get_user_family_id(user_id)
    if family_id:
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
    else:
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
    conn.close()

    if period == 'weekly':
        date_filter = datetime.now() - pd.Timedelta(days=7)
    elif period == 'monthly':
        date_filter = datetime.now() - pd.Timedelta(days=30)
    else:
        logging.error("Invalid period specified.")
        return None

    # Convert 'date' columns to datetime
    df_income['date'] = pd.to_datetime(df_income['date'])
    df_expense['date'] = pd.to_datetime(df_expense['date'])

    # Filter data based on date
    recent_income = df_income[df_income['date'] >= date_filter]
    recent_expense = df_expense[df_expense['date'] >= date_filter]

    if recent_income.empty and recent_expense.empty:
        # No data to generate report
        return None

    # Convert 'amount' column to numeric
    recent_income['amount'] = pd.to_numeric(recent_income['amount'], errors='coerce')
    recent_expense['amount'] = pd.to_numeric(recent_expense['amount'], errors='coerce')

    # Drop rows with NaN amounts
    recent_income = recent_income.dropna(subset=['amount'])
    recent_expense = recent_expense.dropna(subset=['amount'])

    # Prepare text report
    report_lines = []

    # Total amounts
    if language == 'uz':
        income_total = recent_income.groupby('currency')['amount'].sum().reset_index()
        expense_total = recent_expense.groupby('currency')['amount'].sum().reset_index()
        report_lines.append('📊 Umumiy Hisobot:')
        for currency in set(income_total['currency']).union(expense_total['currency']):
            income_sum = income_total[income_total['currency'] == currency]['amount'].sum()
            expense_sum = expense_total[expense_total['currency'] == currency]['amount'].sum()
            balance = income_sum - expense_sum
            report_lines.append(f"💰 Valyuta: {currency}")
            report_lines.append(f"   ➕ Kirim: {income_sum}")
            report_lines.append(f"   ➖ Chiqim: {expense_sum}")
            report_lines.append(f"   💵 Balans: {balance}")
    else:
        income_total = recent_income.groupby('currency')['amount'].sum().reset_index()
        expense_total = recent_expense.groupby('currency')['amount'].sum().reset_index()
        report_lines.append('📊 Общий Отчет:')
        for currency in set(income_total['currency']).union(expense_total['currency']):
            income_sum = income_total[income_total['currency'] == currency]['amount'].sum()
            expense_sum = expense_total[expense_total['currency'] == currency]['amount'].sum()
            balance = income_sum - expense_sum
            report_lines.append(f"💰 Валюта: {currency}")
            report_lines.append(f"   ➕ Доход: {income_sum}")
            report_lines.append(f"   ➖ Расход: {expense_sum}")
            report_lines.append(f"   💵 Баланс: {balance}")

    # Detailed entries (optional)
    # You can add code here to include detailed entries if desired

    return '\n'.join(report_lines)


def create_graph_report(user_id, graph_type, language):
    conn = sqlite3.connect('bot_database.db')
    family_id = get_user_family_id(user_id)
    if family_id:
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE family_id = ? AND approved = 1', conn, params=(family_id,)
        )
    else:
        df_income = pd.read_sql_query(
            'SELECT * FROM incomes WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
        df_expense = pd.read_sql_query(
            'SELECT * FROM expenses WHERE user_id = ? AND approved = 1', conn, params=(user_id,)
        )
    conn.close()

    # Convert 'date' columns to datetime
    df_income['date'] = pd.to_datetime(df_income['date'])
    df_expense['date'] = pd.to_datetime(df_expense['date'])

    if graph_type == 'income_expense_over_time':
        # Group by month
        df_income['month'] = df_income['date'].dt.to_period('M')
        df_expense['month'] = df_expense['date'].dt.to_period('M')

        income_by_month = df_income.groupby('month')['amount'].sum()
        expense_by_month = df_expense.groupby('month')['amount'].sum()

        plt.figure(figsize=(10, 6))
        income_by_month.plot(kind='bar', color='green', label='Income')
        expense_by_month.plot(kind='bar', color='red', label='Expense', alpha=0.7)
        plt.legend()
        plt.title('Income and Expense Over Time')
        plt.xlabel('Month')
        plt.ylabel('Amount')
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        return buffer
    elif graph_type == 'category_distribution':
        # Group by category
        expense_by_category = df_expense.groupby('category')['amount'].sum()
        plt.figure(figsize=(8, 8))
        expense_by_category.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Expense Distribution by Category')
        plt.ylabel('')
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        return buffer
    else:
        return None
