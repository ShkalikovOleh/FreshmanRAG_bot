from typing import List

from langchain_core.documents import Document


def make_html_link(url: str, name: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def make_html_quote(text: str) -> str:
    return f"<blockquote>{text}</blockquote>"


def tg_message_to_source_str(doc: Document) -> str:
    author = doc.metadata["author"]
    title = doc.metadata["title"]

    if doc.metadata["is_public"]:
        link = doc.metadata["source"]
        link_str = make_html_link(link, title)
        return f"{link_str} від {author}"
    else:
        doc_quote = make_html_quote(doc.page_content)
        return f"{title} від {author}: {doc_quote}"


def web_doc_to_source_str(doc: Document) -> str:
    title = doc.metadata["title"]
    link = doc.metadata["source"]
    return make_html_link(link, title)


def docs_to_sources_str(documents: List[Document]) -> str:
    links = set()
    source_text_rows = []
    idx = 1
    for doc in documents:
        if "is_public" in doc.metadata:
            source_str = tg_message_to_source_str(doc)
        elif doc.metadata["source"] in links:
            links.add(doc.metadata["source"])
            source_str = web_doc_to_source_str(doc)
        else:
            continue

        out_row = f"[{idx}] {source_str}"
        source_text_rows.append(out_row)
        idx += 1

    sources_text = "\n".join(source_text_rows)
    return sources_text


def remove_bot_command(message: str, command: str, bot_name: str):
    return message.removeprefix(f"/{command}").removeprefix(bot_name).strip()
