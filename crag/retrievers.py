from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

from bot.utils import cache_once


def get_retriever(retriever_config: dict[str, Any]) -> BaseRetriever:
    k = retriever_config.get("k", 4)
    store_type = retriever_config["vector_store_type"]
    store_args = retriever_config["vector_store_args"]
    emb_type = retriever_config["embeeddings_type"]
    emb_args = retriever_config["embeeddings_args"]

    embeddings = get_embeddings(emb_type, **emb_args)
    vectorstore = get_vectorstore(store_type, embeddings, **store_args)

    retriever = vectorstore.as_retriever(k=k)
    return retriever


def get_embeddings(emb_type: str, **emb_args) -> Embeddings:
    match emb_type:
        case "hugging_face":
            return get_hf_embeeddings(**emb_args)
        case _:
            raise ValueError("Unsupported embeddings type")


@cache_once
def get_vectorstore(store_type: str, embeddings: Embeddings | None, **store_args):
    match store_type:
        case "pgvector":
            return get_pgvector_store(embeddings, **store_args)
        case _:
            raise ValueError("Unsupported vectore store type")


def get_pgvector_store(embeddings, **kwargs) -> VectorStore:
    from langchain_postgres import PGVector

    collection_name = "FreshmanRAG"
    vectorstore = PGVector(
        embeddings=embeddings, collection_name=collection_name, use_jsonb=True, **kwargs
    )

    return vectorstore


def get_hf_embeeddings(**kwargs) -> Embeddings:
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(**kwargs)

    return embeddings
