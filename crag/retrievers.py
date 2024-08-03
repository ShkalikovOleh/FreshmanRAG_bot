from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever


def get_retriever(retriever_config: dict[str, Any]) -> BaseRetriever:
    store_type = retriever_config["vector_store_type"]
    store_args = retriever_config["vector_store_args"]
    emb_type = retriever_config["embeeddings_type"]
    emb_args = retriever_config["embeeddings_args"]

    match emb_type:
        case "hugging_face":
            embeddings = get_hf_embeeddings(**emb_args)
        case _:
            raise ValueError("Unsupported embeddings type")

    match store_type:
        case "pgvector":
            return get_postgres_retriever(embeddings, **store_args)
        case _:
            raise ValueError("Unsupported vectore store type")


def get_postgres_retriever(embeddings, **kwargs) -> BaseRetriever:
    from langchain_postgres import PGVector

    k = kwargs.pop("k", 3)

    collection_name = "FreshmanRAG"
    vectorstore = PGVector(
        embeddings=embeddings, collection_name=collection_name, use_jsonb=True, **kwargs
    )

    retriever = vectorstore.as_retriever(k=k)
    return retriever


def get_hf_embeeddings(**kwargs) -> Embeddings:
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(**kwargs)

    return embeddings
