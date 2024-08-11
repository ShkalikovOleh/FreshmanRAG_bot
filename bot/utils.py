from typing import List

from langchain_core.documents import Document


def make_html_link(url: str, name: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def make_html_quote(text: str) -> str:
    return f"<blockquote>{text}</blockquote>"


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


def remove_bot_command(message: str, command: str, bot_name: str):
    return message.removeprefix(f"/{command}").removeprefix(bot_name).strip()
