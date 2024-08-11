from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


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
