from typing import List

from langchain_core.documents import Document
from sqlalchemy.future import select
from telegram.constants import ChatType

from bot.db import Admin, BannedUserOrChat


def make_html_link(url: str, name: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def docs_to_sources_str(documents: List[Document]) -> str:
    links = set()
    source_text_rows = []
    for doc in documents:
        title = doc.metadata["title"]

        if "is_public" in doc.metadata and not doc.metadata["is_public"]:
            link = doc.metadata.get("public_source", None)
        else:
            link = doc.metadata["source"]

        author = doc.metadata.get("author", None)

        if link is not None:
            if link in links:
                continue
            links.add(link)
            citation = make_html_link(link, title)
            if author is not None:
                citation += f" від {author}"
        else:
            citation = title + f" від {author}:" + "\n\n" + doc.page_content + "\n"

        idx = len(source_text_rows) + 1
        out_row = f"[{idx}] {citation}"
        source_text_rows.append(out_row)

    sources_text = "\n".join(source_text_rows)
    return sources_text


def cache_once(f):
    prev_res = None

    def wrapped(*args, **kwargs):
        nonlocal prev_res
        if prev_res is None:
            prev_res = f(*args, **kwargs)
        return prev_res

    return wrapped


def with_db_session(session_param_name="db_session"):
    def decorator(handler):
        async def wrapper(*args, **kwargs):
            db_session = kwargs.pop(session_param_name)
            async with db_session() as session:
                kwargs[session_param_name] = session
                await handler(*args, **kwargs)

        return wrapper

    return decorator


def admin_only(
    session_param_name="db_session",
    should_can_add_info=True,
    should_can_add_admins=True,
):
    def decorator(handler):
        async def wrapper(*args, **kwargs):
            update, context = args
            session = kwargs[session_param_name]

            admin = await session.get(Admin, update.effective_user.id)
            if (
                admin is None
                or (should_can_add_info and not admin.can_add_info)
                or (should_can_add_admins and not admin.can_add_new_admins)
            ):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.effective_message.id,
                    text="У вас недостатньо прав для цієї дії (:",
                )
                return
            else:
                await handler(*args, **kwargs)

        return wrapper

    return decorator


def filter_banned(session_param_name="db_session"):
    def decorator(handler):
        async def wrapper(*args, **kwargs):
            update, _ = args
            session = kwargs[session_param_name]

            banned_user = await session.get(BannedUserOrChat, update.effective_user.id)
            if banned_user is not None:
                return

            # check whether chat is banned iff chat is a group
            chat_type = update.effective_chat.type
            if chat_type == ChatType.GROUP or chat_type == ChatType.SUPERGROUP:
                banned_chat_query = (
                    select(BannedUserOrChat)
                    .where(BannedUserOrChat.tg_id == update.effective_chat.id)
                    .where(not BannedUserOrChat.is_user)
                )
                banned_chat = await session.scalar(banned_chat_query)
                if banned_chat is not None:
                    return

            await handler(*args, **kwargs)

        return wrapper

    return decorator
