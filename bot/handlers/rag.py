from langchain_core.runnables import Runnable
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.decorators import filter_banned, with_db_session
from bot.utils import docs_to_sources_str, make_html_quote


async def infer_graph(graph: Runnable, question: str, only_docs: bool = False) -> str:
    response = await graph.ainvoke(
        {
            "question": question,
            "do_generate": not only_docs,
            "failed": False,
            "remaining_rewrites": 1,
        }
    )
    output = ""

    actual_question = response["question"]
    if not response["failed"] and question != actual_question:
        output += "Змінено питання/запит на:\n"
        output += make_html_quote(actual_question)

    answer = response.get("generation")
    if answer is not None:
        output += answer

    docs = response["documents"]
    if len(docs) > 0:
        sources_text = docs_to_sources_str(docs)
        sources_preambule = "\n\nДжерела/найбільш релевантні посилання:\n"
        output += sources_preambule + sources_text

    return output


@with_db_session()
@filter_banned()
async def answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, graph: Runnable, **kwargs
):
    question = update.effective_message.text.removeprefix("/ans").strip()
    response = await infer_graph(graph, question)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )


@with_db_session()
@filter_banned()
async def answer_to_replied(
    update: Update, context: ContextTypes.DEFAULT_TYPE, graph: Runnable, **kwargs
):
    question = update.effective_message.reply_to_message.text.removeprefix(
        "/ans_rep"
    ).strip()
    response = await infer_graph(graph, question)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.reply_to_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )


@with_db_session()
@filter_banned()
async def retieve_docs(
    update: Update, context: ContextTypes.DEFAULT_TYPE, graph: Runnable, **kwargs
):
    question = update.effective_message.text.removeprefix("/docs").strip()
    response = await infer_graph(graph, question, only_docs=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )


@with_db_session()
@filter_banned()
async def retieve_docs_to_replied(
    update: Update, context: ContextTypes.DEFAULT_TYPE, graph: Runnable, **kwargs
):
    question = update.effective_message.reply_to_message.text.removeprefix(
        "/docs_rep"
    ).strip()
    response = await infer_graph(graph, question, only_docs=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.reply_to_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )
