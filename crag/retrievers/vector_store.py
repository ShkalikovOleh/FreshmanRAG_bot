from typing import List

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from crag.retrievers.base import PipelineRetrieverBase


class VectorStoreRetriever(PipelineRetrieverBase):
    """Creates a Retriever from a given VectorStore by calling as_retriever method"""

    def __init__(self, vector_store: VectorStore, **kwargs) -> None:
        super().__init__()
        self._vector_store = vector_store
        self._retriever = vector_store.as_retriever(**kwargs)

    async def aadd_documents(self, docs: List[Document], **kwargs) -> List[str]:
        return await self._vector_store.aadd_documents(docs, **kwargs)

    async def adelete_documents(self, ids: List[str], **kwargs) -> bool | None:
        return await self._vector_store.adelete(ids, **kwargs)
