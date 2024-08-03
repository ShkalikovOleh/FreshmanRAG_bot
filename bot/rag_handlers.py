from langchain_core.runnables import Runnable
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    graph: Runnable,
):
    question = update.effective_message.text.removeprefix("/ans")
    response = await graph.ainvoke({"question": question})

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text=response["generation"],
        parse_mode=ParseMode.HTML,
    )


async def answer_to_replied(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    graph: Runnable,
):
    question = update.effective_message.reply_to_message.text.removeprefix("/ansrep")
    response = await graph.ainvoke({"question": question})

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.reply_to_message.id,
        text=response["generation"],
        parse_mode=ParseMode.HTML,
    )
