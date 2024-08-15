import logging
import os
from functools import partial
from typing import Callable, List

import hydra
from hydra.utils import call, instantiate
from langchain_core.documents import Document
from langchain_core.runnables import Runnable
from omegaconf import DictConfig
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
)

from bot.db import get_db_sessionmaker
from bot.handlers.management import (
    add_admin,
    add_fact,
    add_fact_from_replied,
    add_facts_from_link,
    ban_user,
    delete_fact,
    unban_user,
)
from bot.handlers.rag import (
    answer,
    answer_to_replied,
    retieve_docs,
    retieve_docs_to_replied,
)
from bot.handlers.service import error, help, reaction, start, unknown
from crag.knowledge.transformations.sequence import TransformationSequence
from crag.retrievers.base import PipelineRetrieverBase

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def prepare_rag_based_handlers(graph: Runnable, db_session: sessionmaker):
    answer_with_graph = partial(answer, graph=graph, db_session=db_session)
    answer_to_replied_with_graph = partial(
        answer_to_replied, graph=graph, db_session=db_session
    )
    retieve_docs_with_graph = partial(retieve_docs, graph=graph, db_session=db_session)
    retieve_docs_to_replied_with_graph = partial(
        retieve_docs_to_replied, graph=graph, db_session=db_session
    )

    return {
        "answer": answer_with_graph,
        "answer_to_replied": answer_to_replied_with_graph,
        "retieve": retieve_docs_with_graph,
        "retieve_to_replied": retieve_docs_to_replied_with_graph,
    }


def prepare_management_handlers(
    pipe_retriever: PipelineRetrieverBase,
    db_session: sessionmaker,
    url_loader: Callable[[List[str]], List[Document]],
    doc_transformator: TransformationSequence,
):
    handlers = {}
    handlers["add_fact"] = partial(
        add_fact,
        pipe_retriever=pipe_retriever,
        db_session=db_session,
        doc_transformator=doc_transformator,
    )
    handlers["add_fact_from_replied"] = partial(
        add_fact_from_replied,
        pipe_retriever=pipe_retriever,
        db_session=db_session,
        doc_transformator=doc_transformator,
    )
    handlers["add_facts_from_link"] = partial(
        add_facts_from_link,
        pipe_retriever=pipe_retriever,
        db_session=db_session,
        url_loader=url_loader,
        doc_transformator=doc_transformator,
    )
    handlers["delete_fact"] = partial(
        delete_fact, pipe_retriever=pipe_retriever, db_session=db_session
    )
    handlers["ban_user"] = partial(ban_user, db_session=db_session)
    handlers["unban_user"] = partial(unban_user, db_session=db_session)
    handlers["add_admin"] = partial(add_admin, db_session=db_session)

    return handlers


def prepare_handlers(config: DictConfig):
    db_session = get_db_sessionmaker(config["bot_db_connection"])
    pipeline = instantiate(config["pipeline"])
    url_loader = call(config["knowledge"]["loader"])
    doc_transformator = call(config["knowledge"]["transform"])

    rag_handlers = prepare_rag_based_handlers(pipeline.graph, db_session)
    manag_handlers = prepare_management_handlers(
        pipeline.pipe_retriever, db_session, url_loader, doc_transformator
    )

    return rag_handlers, manag_handlers


@hydra.main(version_base="1.3", config_path="../configs", config_name="default")
def main(config: DictConfig) -> None:
    rag_handlers, manag_handlers = prepare_handlers(config)

    tgbot_token = os.getenv("TGBOT_TOKEN")
    application = ApplicationBuilder().token(tgbot_token).build()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    reaction_handler = MessageReactionHandler(reaction)

    answer_handler = CommandHandler("ans", rag_handlers["answer"])
    answer_to_replied_handler = CommandHandler(
        "ans_rep", rag_handlers["answer_to_replied"], filters=filters.REPLY
    )
    retieve_docs_handler = CommandHandler("docs", rag_handlers["retieve"])
    retieve_docs_to_replied_handler = CommandHandler(
        "docs_rep", rag_handlers["retieve_to_replied"], filters=filters.REPLY
    )

    private_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND) & filters.ChatType.PRIVATE,
        rag_handlers["answer"],
    )

    add_fact_handler = CommandHandler("add", manag_handlers["add_fact"])
    delete_fact_handler = CommandHandler("del", manag_handlers["delete_fact"])
    add_fact_from_replied_handler = CommandHandler(
        "add_rep", manag_handlers["add_fact_from_replied"]
    )
    add_facts_from_link_handler = CommandHandler(
        "add_link", manag_handlers["add_facts_from_link"]
    )
    ban_handler = CommandHandler("ban", manag_handlers["ban_user"])
    unban_handler = CommandHandler("unban", manag_handlers["unban_user"])
    add_admin_handler = CommandHandler("add_admin", manag_handlers["add_admin"])

    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(reaction_handler)
    application.add_handler(answer_handler)
    application.add_handler(answer_to_replied_handler)
    application.add_handler(retieve_docs_handler)
    application.add_handler(retieve_docs_to_replied_handler)
    application.add_handler(private_message_handler)
    application.add_handler(add_fact_handler)
    application.add_handler(add_fact_from_replied_handler)
    application.add_handler(delete_fact_handler)
    application.add_handler(add_facts_from_link_handler)
    application.add_handler(ban_handler)
    application.add_handler(unban_handler)
    application.add_handler(add_admin_handler)
    application.add_handler(unknown_handler)

    application.add_error_handler(error)

    application.run_polling(allowed_updates=Update.MESSAGE)


if __name__ == "__main__":
    main()
