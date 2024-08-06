from typing import Any, List

from langchain.base_language import BaseLanguageModel
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from crag.llms import get_llm
from crag.prompts import get_docs_filtering_prompt, get_rag_prompt
from crag.retrievers import get_retriever


def get_graph(config: dict[str, Any]) -> Runnable:
    llm = get_llm(config["llm_config"])
    retriever = get_retriever(config["retriever_config"])

    type = config["graph_type"]
    match type:
        case "simple_rag":
            graph = simple_rag_graph(llm, retriever, config)
        case "simple_rag_with_docs_filtering":
            graph = simple_rag_with_docs_filtering(llm, retriever, config)
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


async def decide_to_generate_with_filtering(state):
    if len(state["documents"]) == 0:
        return "giveup"
    elif state["do_generate"]:
        return "generate"
    else:
        return "stop"


async def giveup(state):
    question = state["question"]

    response = (
        "Вибачте, на жаль я не можу знайти жодного релевантного документа, "
        "який стосується вашого запиту"
    )

    return {"question": question, "generation": response}


def documents_to_context_str(docs: List[Document]):
    return "\n\n".join(doc.page_content for doc in docs)


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

        context = documents_to_context_str(documents)
        generation = await rag_chain.ainvoke({"context": context, "question": question})

        return {
            "documents": documents,
            "question": question,
            "generation": generation,
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


def simple_rag_with_docs_filtering(
    llm: BaseLanguageModel, retriever: BaseRetriever, config: dict[str, Any]
) -> StateGraph:
    llm_type = config["llm_config"]["llm_type"]

    rag_prompt = get_rag_prompt(llm_type)
    rag_chain = rag_prompt | llm | StrOutputParser()

    filtering_prompt = get_docs_filtering_prompt(llm_type)
    filter_chain = filtering_prompt | llm | JsonOutputParser()

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

        context = documents_to_context_str(documents)
        generation = await rag_chain.ainvoke({"context": context, "question": question})

        return {
            "documents": documents,
            "question": question,
            "generation": generation,
        }

    async def grade_documents(state):
        question = state["question"]
        documents = state["documents"]
        do_generate = state["do_generate"]

        relevant_docs = []
        for doc in documents:
            result = await filter_chain.ainvoke(
                {"document": doc.page_content, "question": question}
            )
            if result["score"]:
                relevant_docs.append(doc)

        return {
            "documents": relevant_docs,
            "question": question,
            "do_generate": do_generate,
        }

    workflow = StateGraph(SimpleRagGraphState)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("giveup", giveup)
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate_with_filtering,
        {
            "giveup": "giveup",
            "generate": "generate",
            "stop": END,
        },
    )
    workflow.add_edge("giveup", END)
    workflow.add_edge("generate", END)

    return workflow
