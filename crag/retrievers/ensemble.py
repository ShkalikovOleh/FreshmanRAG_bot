from typing import List

from langchain.retrievers import EnsembleRetriever as LangchainEnsembleRetriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from crag.retrievers.base import PipelineRetrieverBase


class EnsembleRetriever(PipelineRetrieverBase):
    """Wrapper around langchain.retrievers.EnsembleRetriever that implements
    functionality to add"""

    def __init__(
        self,
        retrievers: List[PipelineRetrieverBase | BaseRetriever],
        weights: List[float] | None = None,
        c: int = 60,
        id_key: str | None = None,
    ) -> None:
        super().__init__()
        base_retrievers = [retriever.retriever for retriever in retrievers]
        self._retriever = LangchainEnsembleRetriever(
            retrievers=base_retrievers, c=c, id_key=id_key
        )
        if weights is not None:
            self._retriever.weights = weights
        self._child_retrievers = retrievers

    async def aadd_documents(self, docs: List[Document], **kwargs) -> List[str]:
        ids = await self._child_retrievers[0].aadd_documents(docs)
        for base_retriever in self._child_retrievers[1:]:
            await base_retriever.aadd_documents(docs, ids=ids)
        return ids

    async def adelete_documents(self, ids: List[str], **kwargs) -> bool | None:
        result = True
        for base_retriever in self._child_retrievers:
            result = result and await base_retriever.adelete_documents(ids)
        return result
