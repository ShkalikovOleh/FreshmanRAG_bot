from typing import List

import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import HTMLSectionSplitter, RecursiveCharacterTextSplitter


def load_telegraph_guides(urls: List[str], split_headers: bool = False):
    if split_headers:
        html_docs = load_urls(urls)
        headers = split_headers(html_docs)
        docs = filter_telegram_header_splits(headers)
    else:
        docs_list = [WebBaseLoader(url).load() for url in urls]
        docs = [item for sublist in docs_list for item in sublist]

    docs = split_into_chunks(docs)
    return docs


def load_urls(urls: List[str]):
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


def split_headers(html_docs: List[Document]) -> List[Document]:
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    html_splitter = HTMLSectionSplitter(headers_to_split_on=headers_to_split_on)
    html_header_splits = html_splitter.split_documents(html_docs)
    return html_header_splits


def filter_telegram_header_splits(html_header_splits: List[Document]) -> List[Document]:
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


def split_into_chunks(docs: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=25
    )
    chunked_docs = text_splitter.split_documents(docs)
    return chunked_docs
