from langchain_core.runnables import Runnable
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    graph: Runnable,
):
    response = await graph.ainvoke({"question": update.effective_message.text})

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response["generation"],
        parse_mode=ParseMode.HTML,
    )
