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
        chat_id=update.effective_chat.id,
        text=(
            "Цей бот підтримує наступні користувацькі команди:\n\n"
            "/start - Показати опис бота\n"
            "/help - Показати доступні команди\n"
            "/ans - Відповісти на питання\n"
            "/ans_rep - Відповісти на питання з replied повідомлення\n"
            "/docs - Надати релевантні посилання\n"
            "/docs_rep - Надати релевантні посилання для replied повідомлення"
        ),
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Вибачте, вказана команда не підтримується.",
    )


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.error)
