from langchain_core.runnables import Runnable
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.utils import docs_to_sources_str


async def infer_graph(graph: Runnable, question: str) -> str:
    response = await graph.ainvoke({"question": question})
    answer = response["generation"]
    sources_text = docs_to_sources_str(response["documents"])
    return answer + sources_text


async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    graph: Runnable,
):
    question = update.effective_message.text.removeprefix("/ans")
    response = await infer_graph(graph, question)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )


async def answer_to_replied(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    graph: Runnable,
):
    question = update.effective_message.reply_to_message.text.removeprefix("/ans_rep")
    response = await infer_graph(graph, question)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.reply_to_message.id,
        text=response,
        parse_mode=ParseMode.HTML,
    )
