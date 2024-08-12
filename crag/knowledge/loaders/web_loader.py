from typing import List

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document


def load(urls: List[str], **kwargs) -> List[Document]:
    """Load and parse into text given URLs"""

    docs_list = [WebBaseLoader(url, **kwargs).load() for url in urls]
    docs = [item for sublist in docs_list for item in sublist]
    return docs
