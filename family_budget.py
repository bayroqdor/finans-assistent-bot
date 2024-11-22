# family_budget.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db_functions import get_user_language
from utilities import delete_previous_bot_message
from language_data import languages
import sqlite3
from telegram.ext import CallbackContext
import logging

def notify_family_head(family_id, transaction_id, transaction_type, member_id):
    # Get head_id from families table
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT head_id FROM families WHERE family_id = ?', (family_id,))
    result = c.fetchone()
    conn.close()
    if result:
        head_id = result[0]
        # Send approval request to head
        language = get_user_language(head_id)
        member_language = get_user_language(member_id)
        message_text = f"Yangi {transaction_type} kiritildi. Tasdiqlaysizmi?"
        keyboard = [
            [
                InlineKeyboardButton(languages[language]['approve_expense'], callback_data=f'approve_{transaction_type}_{transaction_id}_{member_id}'),
                InlineKeyboardButton(languages[language]['reject_expense'], callback_data=f'reject_{transaction_type}_{transaction_id}_{member_id}'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # We need to get the bot instance from somewhere
        # For simplicity, let's assume we have access to the context
        # If not, you may need to refactor the code to pass the bot instance
        try:
            bot = CallbackContext.bot
            bot.send_message(chat_id=head_id, text=message_text, reply_markup=reply_markup)
        except Exception as e:
            logging.error(f"Error sending message to family head: {e}")


def handle_approval(update, context):
    from db_functions import get_user_language, approve_transaction, reject_transaction
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    if data.startswith('approve_'):
        _, transaction_type, transaction_id, member_id = data.split('_')
        approve_transaction(transaction_id, transaction_type)
        query.answer(text=languages[language]['expense_approved'])
        # Notify member
        member_language = get_user_language(int(member_id))
        context.bot.send_message(chat_id=int(member_id), text=languages[member_language]['expense_approved'])
    elif data.startswith('reject_'):
        _, transaction_type, transaction_id, member_id = data.split('_')
        reject_transaction(transaction_id, transaction_type)
        query.answer(text=languages[language]['expense_rejected'])
        # Notify member
        member_language = get_user_language(int(member_id))
        context.bot.send_message(chat_id=int(member_id), text=languages[member_language]['expense_rejected'])
    delete_previous_bot_message(update, context)
