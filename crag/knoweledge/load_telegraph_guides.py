import argparse
import asyncio
from typing import List

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import HTMLSectionSplitter, RecursiveCharacterTextSplitter

from bot.utils import load_config
from crag.retrievers import get_embeddings, get_vectorstore


def load_telegraph_guides(urls: List[str]):
    html_docs = load_urls(urls)
    headers = split_headers(html_docs)
    filtered_headers = filter_telegram_header_splits(headers)
    docs = split_into_chunks(filtered_headers)
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
        chunk_size=500, chunk_overlap=50
    )
    chunked_docs = text_splitter.split_documents(docs)
    return chunked_docs


async def main(cfg: argparse.Namespace) -> None:
    with open(cfg.urls) as f:
        urls = [line.strip() for line in f.readlines()]
        docs = load_telegraph_guides(urls)

        config = load_config()

        emb_type = config["retriever_config"]["embeeddings_type"]
        emb_args = config["retriever_config"]["embeeddings_args"]
        embeddings = get_embeddings(emb_type, **emb_args)

        store_type = config["retriever_config"]["vector_store_type"]
        store_args = config["retriever_config"]["vector_store_args"]
        vectorstore = get_vectorstore(store_type, embeddings, **store_args)

        await vectorstore.aadd_documents(docs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Adds given telegraph guides to the knoweledge base"
    )
    parser.add_argument("--urls", type=str, help="File with links to guides")

    cfg = parser.parse_args()

    asyncio.run(main(cfg))
