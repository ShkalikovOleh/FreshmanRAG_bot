import json
import logging
import os
from functools import partial
from typing import Any

from sqlalchemy.orm import sessionmaker
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.db import get_db_sessionmaker
from bot.management_handlers import (
    add_admin,
    add_fact,
    add_public_source_to_fact,
    ban_user,
    unban_user,
)
from bot.rag_handlers import answer, answer_to_replied
from bot.service_handlers import error, help, start, unknown
from crag.graphs import get_graph
from crag.retrievers import get_vectorstore

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def load_config() -> dict[str, Any]:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(root_dir, "config.json")
    with open(cfg_path) as file:
        cfg = json.load(file)

    return cfg


def prepare_rag_based_handlers(config: dict[str, Any], db_session: sessionmaker):
    graph = get_graph(config)

    answer_with_graph = partial(answer, graph=graph, db_session=db_session)
    answer_to_replied_with_graph = partial(
        answer_to_replied, graph=graph, db_session=db_session
    )

    return {
        "answer": answer_with_graph,
        "answer_to_replied": answer_to_replied_with_graph,
    }


def prepare_management_handlers(config: dict[str, Any], db_session: sessionmaker):
    store_type = config["retriever_config"]["vector_store_type"]
    store_args = config["retriever_config"]["vector_store_args"]
    vectorstore = get_vectorstore(store_type, None, **store_args)

    handlers = {}
    handlers["add_fact"] = partial(
        add_fact, vector_store=vectorstore, db_session=db_session
    )
    handlers["ban_user"] = partial(ban_user, db_session=db_session)
    handlers["unban_user"] = partial(unban_user, db_session=db_session)
    handlers["add_admin"] = partial(add_admin, db_session=db_session)
    handlers["add_source_for_fact"] = partial(
        add_public_source_to_fact, db_session=db_session
    )

    return handlers


if __name__ == "__main__":
    config = load_config()
    db_session = get_db_sessionmaker(config["db_connection"])
    rag_handlers = prepare_rag_based_handlers(config, db_session)
    manag_handlers = prepare_management_handlers(config, db_session)

    tgbot_token = os.getenv("TGBOT_TOKEN")
    application = ApplicationBuilder().token(tgbot_token).build()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)

    answer_handler = CommandHandler("ans", rag_handlers["answer"])
    answer_to_replied_handler = CommandHandler(
        "ans_rep", rag_handlers["answer_to_replied"], filters=filters.REPLY
    )

    private_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND) & filters.ChatType.PRIVATE,
        rag_handlers["answer"],
    )

    add_fact_handler = CommandHandler("add", manag_handlers["add_fact"])
    add_source_for_fact_handler = CommandHandler(
        "add_source", manag_handlers["add_source_for_fact"]
    )
    ban_handler = CommandHandler("ban", manag_handlers["ban_user"])
    unban_handler = CommandHandler("unban", manag_handlers["unban_user"])
    add_admin_handler = CommandHandler("add_admin", manag_handlers["add_admin"])

    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(answer_handler)
    application.add_handler(answer_to_replied_handler)
    application.add_handler(private_message_handler)
    application.add_handler(add_fact_handler)
    application.add_handler(add_source_for_fact_handler)
    application.add_handler(ban_handler)
    application.add_handler(unban_handler)
    application.add_handler(add_admin_handler)
    application.add_handler(unknown_handler)

    application.add_error_handler(error)

    application.run_polling()
