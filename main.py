# main.py

import logging
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from handlers import (
    start,
    language_selection,
    main_menu_selection,
    income_start,
    income_amount_received,
    income_currency_received,
    income_category_received,
    income_comment_received,
    expense_start,
    expense_amount_received,
    expense_currency_received,
    expense_category_received,
    expense_comment_received,
    report_start,
    report_selection,
    report_action_selection,
    graph_report_selection,
    family_budget_menu_selection,
    family_create,
    family_join,
    family_budget_actions,
    family_budget_set_amount,
    settings_selection,
    cancel,
    family_budget_start, settings,
)
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
from db_functions import init_db
from constants import TOKEN
from language_data import languages
from family_budget import handle_approval

logging.basicConfig(level=logging.INFO)

def main():
    init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler for language selection
    lang_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE_SELECTION: [
                CallbackQueryHandler(language_selection, pattern='^lang_(uz|ru)$')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    dp.add_handler(lang_conv_handler)

    # Conversation handlers for income
    income_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex('^(' + languages['uz']['income'] + '|' + languages['ru']['income'] + ')$'),
                income_start,
            )
        ],
        states={
            INCOME_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, income_amount_received)],
            INCOME_CURRENCY: [CallbackQueryHandler(income_currency_received, pattern='.*')],
            INCOME_CATEGORY: [CallbackQueryHandler(income_category_received, pattern='.*')],
            INCOME_COMMENT: [MessageHandler(Filters.text & ~Filters.command, income_comment_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(income_conv_handler)

    # Conversation handlers for expense
    expense_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex('^(' + languages['uz']['expense'] + '|' + languages['ru']['expense'] + ')$'),
                expense_start,
            )
        ],
        states={
            EXPENSE_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, expense_amount_received)],
            EXPENSE_CURRENCY: [CallbackQueryHandler(expense_currency_received, pattern='.*')],
            EXPENSE_CATEGORY: [CallbackQueryHandler(expense_category_received, pattern='.*')],
            EXPENSE_COMMENT: [MessageHandler(Filters.text & ~Filters.command, expense_comment_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(expense_conv_handler)

    # Conversation handler for report
    report_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex('^(' + languages['uz']['report'] + '|' + languages['ru']['report'] + ')$'),
                report_start,
            )
        ],
        states={
            REPORT_SELECTION: [CallbackQueryHandler(report_selection, pattern='.*')],
            REPORT_ACTION_SELECTION: [CallbackQueryHandler(report_action_selection, pattern='.*')],
            GRAPH_REPORT_SELECTION: [CallbackQueryHandler(graph_report_selection, pattern='.*')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(report_conv_handler)

    # Conversation handler for family budget
    family_budget_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex('^(' + languages['uz']['family_budget'] + '|' + languages['ru']['family_budget'] + ')$'),
                family_budget_start,
            )
        ],
        states={
            FAMILY_BUDGET_MENU: [MessageHandler(Filters.text & ~Filters.command, family_budget_menu_selection)],
            FAMILY_CREATE: [MessageHandler(Filters.text & ~Filters.command, family_create)],
            FAMILY_JOIN: [MessageHandler(Filters.text & ~Filters.command, family_join)],
            FAMILY_BUDGET_ACTIONS: [MessageHandler(Filters.text & ~Filters.command, family_budget_actions)],
            FAMILY_BUDGET_SET_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, family_budget_set_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(family_budget_conv_handler)

    # Conversation handler for settings
    settings_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex('^(' + languages['uz']['settings'] + '|' + languages['ru']['settings'] + ')$'),
                settings,
            )
        ],
        states={
            SETTINGS_SELECTION: [CallbackQueryHandler(settings_selection, pattern='.*')],
            LANGUAGE_SELECTION: [
                CallbackQueryHandler(language_selection, pattern='^lang_(uz|ru)$')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(settings_conv_handler)

    # Handler for main menu selections
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, main_menu_selection))

    # Handler for approvals
    dp.add_handler(CallbackQueryHandler(handle_approval, pattern='^(approve|reject)_.*'))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
