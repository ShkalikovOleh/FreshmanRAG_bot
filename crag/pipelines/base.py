from abc import ABC, abstractmethod
from typing import List, TypedDict

from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph

from crag.retrievers.base import PipelineRetrieverBase


class PipelineBase(ABC):

    @property
    @abstractmethod
    def pipe_retriever(self) -> PipelineRetrieverBase:
        pass

    @property
    @abstractmethod
    def llm(self) -> BaseLanguageModel:
        pass

    @property
    def graph(self) -> Runnable:
        graph = self.construct_graph()
        compiled_graph = graph.compile()
        return compiled_graph

    @abstractmethod
    def construct_graph(self) -> StateGraph:
        pass


class SimpleRagGraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    do_generate: bool
    failed: bool = False


async def giveup(state: SimpleRagGraphState) -> SimpleRagGraphState:
    response = (
        "Вибачте, на жаль я не можу знайти жодного релевантного документа, "
        "який стосується вашого запиту (:"
    )

    state["generation"] = response
    state["failed"] = True
    return state


def documents_to_context_str(docs: List[Document]):
    return "\n\n".join(doc.page_content for doc in docs)
