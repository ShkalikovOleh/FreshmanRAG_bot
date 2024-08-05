from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import Admin, BannedUserOrChat
from bot.utils import admin_only, with_db_session


@with_db_session()
@admin_only(should_can_add_admins=False)
async def add_fact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    vector_store: VectorStore,
    **kwargs,
):
    info = update.effective_message.text_html_urled.removeprefix("/add").strip()

    user_tag = update.effective_user.name
    if user_tag is None:
        user_tag = update.effective_user.full_name
    message_link = update.effective_message.link
    if message_link is None:
        message_link = ""

    doc = Document(
        page_content=info,
        metadata={
            "source": message_link,
            "author": user_tag,
            "title": f"Повідомлення у TG від {user_tag}",
        },
    )
    await vector_store.aadd_documents([doc])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text="Інформацію успішно додано до бази знань",
    )


async def get_user_id_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banned_user_id = None
    if len(context.args) == 1:
        id = context.args[0]
        if id.isdigit():
            banned_user_id = int(id)
    else:
        reply = update.effective_message.reply_to_message
        if reply is not None:
            banned_user_id = reply.from_user.id

    if banned_user_id is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text="Неправильний формат аргументів. Будь ласка, зазначте id "
            "користувача або напишіть цю команду у відповідь на його повідомдення.",
        )

    return banned_user_id


@with_db_session()
@admin_only(should_can_add_admins=False, should_can_add_info=False)
async def ban_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, db_session: AsyncSession
):
    banned_user_id = await get_user_id_from_message(update, context)
    if banned_user_id is None:
        return

    # don't ban admins
    admin_id = update.effective_user.id
    banned_admin = await db_session.get(Admin, banned_user_id)
    if banned_admin is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text="Неможливо забанити адмінів.",
        )
        return

    # actual ban
    banned_user = BannedUserOrChat(
        tg_id=banned_user_id, is_user=True, banned_by_id=admin_id
    )
    db_session.add(banned_user)
    await db_session.commit()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.id,
        text="Вказаного користувача було забанено!",
    )


@with_db_session()
@admin_only(should_can_add_admins=False, should_can_add_info=False)
async def unban_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, db_session: AsyncSession
):
    banned_user_id = await get_user_id_from_message(update, context)
    if banned_user_id is None:
        return

    stmt = delete(BannedUserOrChat).where(BannedUserOrChat.tg_id == banned_user_id)
    result = await db_session.execute(stmt)
    await db_session.commit()

    if result.rowcount > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text="Вказаного користувача було розбанено!",
        )
