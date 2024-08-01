from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Вітаю, я заснований на RAG бот, який намагається дати відповіді на "
        "поширенні питання першачків! Я трошки дурненький, бо відповіді надає LLM, "
        "тож завжди перевіряйте вказані джерела інформації.",
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="У розробці :)"
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Вибачте, вказана команда не підтримується.",
    )


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # do nothing as for now
    pass
