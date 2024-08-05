from typing import Any, List

from langchain.base_language import BaseLanguageModel
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from crag.llms import get_llm
from crag.prompts import get_rag_prompt
from crag.retrievers import get_retriever


def get_graph(config: dict[str, Any]) -> Runnable:
    llm = get_llm(config["llm_config"])
    retriever = get_retriever(config["retriever_config"])

    type = config["graph_type"]
    match type:
        case "simple_rag":
            graph = simple_rag_graph(llm, retriever, config)
        case _:
            raise ValueError("Unsupported graph type")

    compiled_graph = graph.compile()
    return compiled_graph


class SimpleRagGraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    do_generate: bool


async def decide_to_generate(state):
    if state["do_generate"]:
        return "generate"
    else:
        return "stop"


def simple_rag_graph(
    llm: BaseLanguageModel, retriever: BaseRetriever, config: dict[str, Any]
) -> StateGraph:
    prompt = get_rag_prompt(config["llm_config"]["llm_type"])
    rag_chain = prompt | llm | StrOutputParser()

    async def retrieve(state):
        question = state["question"]
        do_generate = state["do_generate"]
        documents = await retriever.ainvoke(question)
        return {
            "documents": documents,
            "question": question,
            "do_generate": do_generate,
        }

    async def generate(state):
        question = state["question"]
        documents = state["documents"]
        do_generate = state["do_generate"]
        generation = await rag_chain.ainvoke(
            {"context": documents, "question": question}
        )
        return {
            "documents": documents,
            "question": question,
            "generation": generation,
            "do_generate": do_generate,
        }

    workflow = StateGraph(SimpleRagGraphState)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        decide_to_generate,
        {
            "stop": END,
            "generate": "generate",
        },
    )
    workflow.add_edge("generate", END)

    return workflow
