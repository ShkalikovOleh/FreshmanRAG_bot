import logging
import os
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
)

from bot.rag_handlers import answer
from bot.service_handlers import start, help, unknown, error

from bot.custom_filters import FilterIsPrivateChat

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


if __name__ == "__main__":
    tgbot_token = os.getenv("TGBOT_TOKEN")
    application = ApplicationBuilder().token(tgbot_token).build()

    private_chat_filter = FilterIsPrivateChat()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)

    answer_handler = CommandHandler("ans", answer)
    private_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND) & private_chat_filter, answer
    )

    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(answer_handler)
    application.add_handler(private_message_handler)
    application.add_handler(unknown_handler)

    application.add_error_handler(error)

    application.run_polling()
