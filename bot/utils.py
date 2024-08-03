from typing import List

from langchain_core.documents import Document


def make_html_link(url: str, name: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def docs_to_sources_str(documents: List[Document]) -> str:
    links = set()
    source_text_rows = []
    for doc in documents:
        link = doc.metadata["source"]
        if link in links:
            continue

        links.add(link)
        title = doc.metadata["title"]
        url_text = make_html_link(link, title)

        idx = len(links)
        out_row = f"[{idx}] {url_text}"
        source_text_rows.append(out_row)

    sources_text = "\n\nДжерела/найбільш релевантні посилання:\n" + "\n".join(
        source_text_rows
    )
    return sources_text
