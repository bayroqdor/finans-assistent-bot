# handlers.py
import sqlite3
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
)
from db_functions import (
    init_db,
    get_user_language,
    set_user_language,
    is_first_time_user,
    save_income,
    save_expense,
    create_family,
    join_family,
    get_user_role,
    get_user_family_id,
    set_user_budget,
)
from language_data import languages
from utilities import delete_previous_bot_message, delete_user_message, delete_message
from report_generation import create_report, create_text_report, create_graph_report
from constants import (
    LANGUAGE_SELECTION,
    INCOME_AMOUNT,
    INCOME_CURRENCY,
    INCOME_CATEGORY,
    INCOME_COMMENT,
    EXPENSE_AMOUNT,
    EXPENSE_CURRENCY,
    EXPENSE_CATEGORY,
    EXPENSE_COMMENT,
    REPORT_SELECTION,
    REPORT_ACTION_SELECTION,
    GRAPH_REPORT_SELECTION,
    FAMILY_BUDGET_MENU,
    FAMILY_CREATE,
    FAMILY_JOIN,
    FAMILY_BUDGET_ACTIONS,
    FAMILY_BUDGET_SET_AMOUNT,
    SETTINGS_SELECTION,
)
from constants import CURRENCIES

def start(update: Update, context: CallbackContext):
    init_db()
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    if language is None:
        # Ask for language selection
        keyboard = [
            [InlineKeyboardButton("O'zbekcha", callback_data='lang_uz')],
            [InlineKeyboardButton("Русский", callback_data='lang_ru')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = update.message.reply_text(
            "Iltimos, tilni tanlang:\nПожалуйста, выберите язык:", reply_markup=reply_markup
        )
        context.user_data['last_bot_message_id'] = message.message_id
        return LANGUAGE_SELECTION
    else:
        # Proceed to main menu
        show_main_menu(update, context, language)
        return ConversationHandler.END

def language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    data = query.data
    if data == 'lang_uz':
        set_user_language(user_id, 'uz')
        language = 'uz'
    elif data == 'lang_ru':
        set_user_language(user_id, 'ru')
        language = 'ru'
    else:
        # Should not happen
        language = 'uz'
    delete_previous_bot_message(update, context)
    show_main_menu(update, context, language)
    return ConversationHandler.END

def show_main_menu(update: Update, context: CallbackContext, language):
    keyboard = [
        [languages[language]['income'], languages[language]['expense']],
        [languages[language]['report'], languages[language]['family_budget']],
        [languages[language]['settings']],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    chat_id = update.effective_chat.id

    user_id = update.effective_user.id
    first_time = is_first_time_user(user_id)

    if first_time:
        message_text = languages[language]['start_message_new']
        # Update first_time to False after greeting
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute('UPDATE users SET first_time = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    else:
        message_text = languages[language]['start_message_returning']

    message = context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
    context.user_data['last_bot_message_id'] = message.message_id

def main_menu_selection(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    delete_user_message(update, context)
    delete_previous_bot_message(update, context)

    if user_input == languages[language]['income']:
        context.user_data.clear()
        income_start(update, context)
    elif user_input == languages[language]['expense']:
        context.user_data.clear()
        expense_start(update, context)
    elif user_input == languages[language]['report']:
        context.user_data.clear()
        report_start(update, context)
    elif user_input == languages[language]['family_budget']:
        context.user_data.clear()
        family_budget_start(update, context)
    elif user_input == languages[language]['settings']:
        context.user_data.clear()
        settings(update, context)
    else:
        # Send a message indicating incorrect selection
        message_text = languages[language]['incorrect_selection']
        chat_id = update.effective_chat.id
        message = context.bot.send_message(chat_id=chat_id, text=message_text)
        context.user_data['last_bot_message_id'] = message.message_id

def income_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [[languages[language]['cancel']]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    message_text = languages[language]['enter_income_amount']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return INCOME_AMOUNT

def income_amount_received(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END

    # Validate that the input is a number
    try:
        amount = float(user_input)
        context.user_data['income_amount'] = amount
        delete_user_message(update, context)
        delete_previous_bot_message(update, context)
    except ValueError:
        # Not a valid number
        delete_user_message(update, context)
        message_text = languages[language]['invalid_amount']
        keyboard = [[languages[language]['cancel']]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup
        )
        context.user_data['last_bot_message_id'] = message.message_id
        return INCOME_AMOUNT

    keyboard = [[InlineKeyboardButton(currency, callback_data=currency)] for currency in CURRENCIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['choose_currency']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return INCOME_CURRENCY

def income_currency_received(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data['income_currency'] = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Prompt for category selection
    categories = languages[language]['income_categories']
    keyboard = []
    for label, data in categories:
        keyboard.append([InlineKeyboardButton(label, callback_data=data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['choose_category']
    message = context.bot.send_message(
        chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return INCOME_CATEGORY

def income_category_received(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data['income_category'] = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [[languages[language]['cancel']]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    message_text = languages[language]['enter_comment']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return INCOME_COMMENT

def income_comment_received(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END

    delete_user_message(update, context)
    delete_previous_bot_message(update, context)
    context.user_data['income_comment'] = user_input
    save_income(user_id, context.user_data)
    # Send notification and delete after 3 seconds
    chat_id = update.effective_chat.id
    message_text = languages[language]['data_saved']
    message = context.bot.send_message(chat_id=chat_id, text=message_text)
    context.job_queue.run_once(
        delete_message, 3, context={'chat_id': chat_id, 'message_id': message.message_id}
    )
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def expense_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [[languages[language]['cancel']]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    message_text = languages[language]['enter_expense_amount']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return EXPENSE_AMOUNT

def expense_amount_received(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END

    # Validate that the input is a number
    try:
        amount = float(user_input)
        context.user_data['expense_amount'] = amount
        delete_user_message(update, context)
        delete_previous_bot_message(update, context)
    except ValueError:
        # Not a valid number
        delete_user_message(update, context)
        message_text = languages[language]['invalid_amount']
        keyboard = [[languages[language]['cancel']]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup
        )
        context.user_data['last_bot_message_id'] = message.message_id
        return EXPENSE_AMOUNT

    keyboard = [[InlineKeyboardButton(currency, callback_data=currency)] for currency in CURRENCIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['choose_currency']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return EXPENSE_CURRENCY

def expense_currency_received(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data['expense_currency'] = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Prompt for category selection
    categories = languages[language]['expense_categories']
    keyboard = []
    for label, data in categories:
        keyboard.append([InlineKeyboardButton(label, callback_data=data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['choose_category']
    message = context.bot.send_message(
        chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return EXPENSE_CATEGORY

def expense_category_received(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data['expense_category'] = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [[languages[language]['cancel']]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    message_text = languages[language]['enter_comment']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return EXPENSE_COMMENT

def expense_comment_received(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END

    delete_user_message(update, context)
    delete_previous_bot_message(update, context)
    context.user_data['expense_comment'] = user_input
    save_expense(user_id, context.user_data)
    # Send notification and delete after 3 seconds
    chat_id = update.effective_chat.id
    message_text = languages[language]['data_saved']
    message = context.bot.send_message(chat_id=chat_id, text=message_text)
    context.job_queue.run_once(
        delete_message, 3, context={'chat_id': chat_id, 'message_id': message.message_id}
    )
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def report_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(languages[language]['weekly'], callback_data='weekly')],
        [InlineKeyboardButton(languages[language]['monthly'], callback_data='monthly')],
        [InlineKeyboardButton(languages[language]['graph_report'], callback_data='graph_report')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['choose_report']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=reply_markup
    )
    context.user_data['last_bot_message_id'] = message.message_id
    return REPORT_SELECTION

def report_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selection = query.data
    context.user_data['report_period'] = selection  # Save the period
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if selection == 'graph_report':
        # Present graph options
        keyboard = [
            [InlineKeyboardButton(languages[language]['income_expense_over_time'], callback_data='income_expense_over_time')],
            [InlineKeyboardButton(languages[language]['category_distribution'], callback_data='category_distribution')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = languages[language]['select_graph_type']
        message = context.bot.send_message(
            chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup
        )
        context.user_data['last_bot_message_id'] = message.message_id
        return GRAPH_REPORT_SELECTION
    else:
        # Present options: View in Telegram or Download
        keyboard = [
            [
                InlineKeyboardButton(languages[language]['view_in_telegram'], callback_data='view_in_telegram'),
                InlineKeyboardButton(languages[language]['download'], callback_data='download'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = languages[language]['select_language']
        message = context.bot.send_message(
            chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup
        )
        context.user_data['last_bot_message_id'] = message.message_id
        return REPORT_ACTION_SELECTION

def report_action_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    action = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    period = context.user_data.get('report_period')

    if action == 'view_in_telegram':
        report_text = create_text_report(user_id, period, language)
        if report_text:
            context.bot.send_message(chat_id=update.effective_chat.id, text=report_text)
        else:
            message_text = languages[language]['no_data']
            message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
            context.user_data['last_bot_message_id'] = message.message_id
    elif action == 'download':
        file_name = create_report(user_id, period, language)
        if file_name and os.path.isfile(file_name):
            with open(file_name, 'rb') as f:
                context.bot.send_document(chat_id=update.effective_chat.id, document=f)
            os.remove(file_name)
        else:
            message_text = languages[language]['no_data']
            message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
            context.user_data['last_bot_message_id'] = message.message_id

    # Send notification and delete after 3 seconds
    chat_id = update.effective_chat.id
    message_text = languages[language]['report_sent']
    message = context.bot.send_message(chat_id=chat_id, text=message_text)
    context.job_queue.run_once(
        delete_message, 3, context={'chat_id': chat_id, 'message_id': message.message_id}
    )
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def graph_report_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    graph_type = query.data
    query.answer()
    delete_previous_bot_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    buffer = create_graph_report(user_id, graph_type, language)
    if buffer:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
        buffer.close()
    else:
        message_text = languages[language]['no_data']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def family_budget_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    role = get_user_role(user_id)

    if role == 'head':
        keyboard = [
            [languages[language]['set_budget']],
            [languages[language]['cancel']],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message_text = languages[language]['select_language']
        chat_id = update.effective_chat.id
        message = context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_BUDGET_ACTIONS
    elif role == 'member':
        message_text = languages[language]['request_sent']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
        # Return to main menu
        show_main_menu(update, context, language)
        return ConversationHandler.END
    else:
        keyboard = [
            [languages[language]['register_family']],
            [languages[language]['join_family']],
            [languages[language]['cancel']],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message_text = languages[language]['select_language']
        chat_id = update.effective_chat.id
        message = context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_BUDGET_MENU

def family_budget_menu_selection(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    delete_user_message(update, context)
    delete_previous_bot_message(update, context)

    if user_input == languages[language]['register_family']:
        # Proceed to family creation
        message_text = "Iltimos, oilangiz nomini kiriting:"
        keyboard = [[languages[language]['cancel']]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_CREATE
    elif user_input == languages[language]['join_family']:
        # Proceed to joining a family
        message_text = "Iltimos, oilangiz ID raqamini kiriting:"
        keyboard = [[languages[language]['cancel']]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_JOIN
    elif user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END
    else:
        message_text = languages[language]['incorrect_selection']
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_BUDGET_MENU

def family_create(update: Update, context: CallbackContext):
    family_name = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    if family_name == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END
    create_family(family_name, user_id)
    message_text = f"Oila yaratildi. Oila ID si: {get_user_family_id(user_id)}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def family_join(update: Update, context: CallbackContext):
    family_id = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    if family_id == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END
    try:
        family_id = int(family_id)
        join_family(user_id, family_id)
        message_text = languages[language]['request_sent']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
    except ValueError:
        message_text = languages[language]['incorrect_selection']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def family_budget_actions(update: Update, context: CallbackContext):
    user_input = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    delete_user_message(update, context)
    delete_previous_bot_message(update, context)

    if user_input == languages[language]['set_budget']:
        message_text = languages[language]['enter_budget_amount']
        keyboard = [[languages[language]['cancel']]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_BUDGET_SET_AMOUNT
    elif user_input == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END
    else:
        message_text = languages[language]['incorrect_selection']
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
        context.user_data['last_bot_message_id'] = message.message_id
        return FAMILY_BUDGET_ACTIONS

def family_budget_set_amount(update: Update, context: CallbackContext):
    amount = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    if amount == languages[language]['cancel']:
        cancel(update, context)
        return ConversationHandler.END
    try:
        amount = float(amount)
        # Set budget for all family members
        family_id = get_user_family_id(user_id)
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE family_id = ? AND role = ?', (family_id, 'member'))
        members = c.fetchall()
        for member in members:
            set_user_budget(member[0], amount)
        conn.close()
        message_text = languages[language]['budget_set']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
    except ValueError:
        message_text = languages[language]['invalid_amount']
        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
        return FAMILY_BUDGET_SET_AMOUNT
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END

def settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    keyboard = [
        [InlineKeyboardButton(languages[language]['change_language'], callback_data='change_language')],
        [InlineKeyboardButton(languages[language]['cancel'], callback_data='cancel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = languages[language]['select_language']
    chat_id = update.effective_chat.id
    message = context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
    context.user_data['last_bot_message_id'] = message.message_id
    return SETTINGS_SELECTION

def settings_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if data == 'change_language':
        # Ask for language selection
        keyboard = [
            [InlineKeyboardButton("O'zbekcha", callback_data='lang_uz')],
            [InlineKeyboardButton("Русский", callback_data='lang_ru')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = languages[language]['choose_language']
        chat_id = update.effective_chat.id
        message = context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
        context.user_data['last_bot_message_id'] = message.message_id
        return LANGUAGE_SELECTION
    elif data == 'cancel':
        delete_previous_bot_message(update, context)
        show_main_menu(update, context, language)
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    delete_previous_bot_message(update, context)
    delete_user_message(update, context)
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    # Send notification and delete after 3 seconds
    chat_id = update.effective_chat.id
    message_text = languages[language]['operation_cancelled']
    message = context.bot.send_message(
        chat_id=chat_id, text=message_text, reply_markup=ReplyKeyboardRemove()
    )
    context.job_queue.run_once(
        delete_message, 3, context={'chat_id': chat_id, 'message_id': message.message_id}
    )
    # Return to main menu
    show_main_menu(update, context, language)
    return ConversationHandler.END
