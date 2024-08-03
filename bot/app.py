import json
import logging
import os
from functools import partial
from typing import Any

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.custom_filters import FilterIsPrivateChat
from bot.rag_handlers import answer
from bot.service_handlers import error, help, start, unknown
from crag.graphs import get_graph

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def load_config() -> dict[str, Any]:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(root_dir, "config.json")
    with open(cfg_path) as file:
        cfg = json.load(file)

    return cfg


def prepare_rag_based_handlers(config: dict[str, Any]):
    graph = get_graph(config)
    answer_with_graph = partial(answer, graph=graph)
    return answer_with_graph


if __name__ == "__main__":
    config = load_config()
    answer_with_graph = prepare_rag_based_handlers(config)

    tgbot_token = os.getenv("TGBOT_TOKEN")
    application = ApplicationBuilder().token(tgbot_token).build()

    private_chat_filter = FilterIsPrivateChat()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)

    answer_handler = CommandHandler("ans", answer_with_graph)
    private_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND) & private_chat_filter, answer_with_graph
    )

    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(answer_handler)
    application.add_handler(private_message_handler)
    application.add_handler(unknown_handler)

    application.add_error_handler(error)

    application.run_polling()
