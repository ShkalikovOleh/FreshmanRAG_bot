from typing import List

from langchain_core.documents import Document


def filter_telegram_headers(html_header_splits: List[Document]) -> List[Document]:
    filtered_docs = []
    prev_source = None
    for doc in html_header_splits:
        doc_text = doc.page_content

        source = doc.metadata["source"]
        is_header = source != prev_source
        prev_source = source

        start_ps = doc_text.find("Більше про можливості реалізації у КПІ")
        if start_ps >= 0:
            doc = doc.copy()
            doc.page_content = doc_text[:start_ps]

        if doc_text.startswith("Report Page") or is_header or start_ps == 0:
            continue

        filtered_docs.append(doc)

    return filtered_docs
