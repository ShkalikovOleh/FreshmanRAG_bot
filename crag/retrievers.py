from abc import ABC, abstractmethod
from typing import List

from langchain.retrievers import EnsembleRetriever as LangchainEnsembleRetriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore


class PipelineRetrieverBase(ABC):
    """The wrapper around Langchain Retriever which gives ability to
    add and delete documents fron an underling store. The main purpose
    of this class is to simplify instantiation from a config file and
    abstract addition and deletion documents in order to do in from the bot.
    """

    _retriever: BaseRetriever

    @property
    def retriever(self) -> BaseRetriever:
        return self._retriever

    @abstractmethod
    async def aadd_documents(self, docs: List[Document], **kwargs) -> List[str]:
        pass

    @abstractmethod
    async def adelete_documents(self, ids: List[str], **kwargs) -> bool | None:
        pass


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


class EnsembleRetriever(PipelineRetrieverBase):
    """Wrapper around langchain.retrievers.EnsembleRetriever that implements
    functionality to add"""

    def __init__(
        self,
        retrievers: List[PipelineRetrieverBase | BaseRetriever],
        weights: List[float],
        c: int = 60,
        id_key: str | None = None,
    ) -> None:
        super().__init__()
        base_retrievers = [retriever.retriever for retriever in retrievers]
        self._retriever = LangchainEnsembleRetriever(
            base_retrievers, weights, c, id_key
        )
        self._child_retrievers = retrievers

    async def aadd_documents(self, docs: List[Document], **kwargs) -> List[str]:
        ids = await self._child_retrievers[0].aadd_documents(docs)
        for base_retriever in self._child_retrievers[1:]:
            await base_retriever.aadd_documents(docs, ids=ids)

    async def adelete_documents(self, ids: List[str], **kwargs) -> bool | None:
        result = True
        for base_retriever in self._child_retrievers:
            result = result and await base_retriever.adelete_documents(ids)
        return result
