from typing import List

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document


def load(urls: List[str]) -> List[Document]:
    """Load plain HTML text but add page title and source to metadatas"""

    html_docs = []
    for url in urls:
        resp = requests.get(url)

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.find("title")

        doc = Document(
            page_content=resp.text, metadata={"title": title.string, "source": url}
        )
        html_docs.append(doc)

    return html_docs
