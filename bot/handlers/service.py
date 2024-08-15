from telegram import Update
from telegram.constants import ParseMode
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


async def reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sometimes Telegram sends message_reaction updates even though the bot asks only
    for message updates. This handler prevents bot to answer twice the same message
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=(
            "Замість того, щоб ставити реакції,"
            " краще б зірочку на GitHub поставили :)"
        ),
        parse_mode=ParseMode.HTML,
    )


async def ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sometimes Telegram sends edited_message updates on simple message reactions
    that cause running all RAG pipeline once again. This handler just ignores all
    edited_message updates
    """
    pass


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.error)
