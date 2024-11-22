# utilities.py

import logging
from telegram import ReplyKeyboardRemove

def delete_previous_bot_message(update, context):
    if 'last_bot_message_id' in context.user_data:
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=context.user_data['last_bot_message_id']
            )
        except Exception as e:
            logging.warning(f"Failed to delete bot message: {e}")


def delete_user_message(update, context):
    try:
        context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )
    except Exception as e:
        logging.warning(f"Failed to delete user message: {e}")


def delete_message(context):
    job = context.job
    chat_id = job.context['chat_id']
    message_id = job.context['message_id']
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")


def sanitize_comment(comment):
    # Limit comment length
    max_length = 200  # Adjust as needed
    sanitized = comment[:max_length]
    # Remove any non-printable characters
    sanitized = ''.join(c for c in sanitized if c.isprintable())
    return sanitized
