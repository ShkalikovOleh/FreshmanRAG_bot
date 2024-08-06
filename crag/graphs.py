from typing import Any, List

from langchain.base_language import BaseLanguageModel
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from crag.llms import get_llm
from crag.prompts import (
    get_docs_filtering_prompt,
    get_question_rewriting_prompt,
    get_rag_prompt,
)
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
        case "rag_with_question_rewriting":
            graph = rag_with_question_rewriting(llm, retriever, config)
        case _:
            raise ValueError("Unsupported graph type")

    compiled_graph = graph.compile()
    return compiled_graph


class SimpleRagGraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    do_generate: bool
    failed: bool = False


async def giveup(state):
    question = state["question"]

    response = (
        "Вибачте, на жаль я не можу знайти жодного релевантного документа, "
        "який стосується вашого запиту (:"
    )

    return {"question": question, "generation": response, "failed": True}


def documents_to_context_str(docs: List[Document]):
    return "\n\n".join(doc.page_content for doc in docs)


def simple_rag_graph(
    llm: BaseLanguageModel, retriever: BaseRetriever, config: dict[str, Any]
) -> StateGraph:
    prompt = get_rag_prompt(config["llm_config"]["llm_type"])
    rag_chain = prompt | llm | StrOutputParser()

    async def retrieve(state):
        question = state["question"]

        documents = await retriever.ainvoke(question)

        state["documents"] = documents
        return state

    async def generate(state):
        question = state["question"]
        documents = state["documents"]

        context = documents_to_context_str(documents)
        generation = await rag_chain.ainvoke({"context": context, "question": question})

        state["generation"] = generation
        return state

    async def decide_to_generate(state):
        if state["do_generate"]:
            return "generate"
        else:
            return "stop"

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

        documents = await retriever.ainvoke(question)

        state["documents"] = documents
        return state

    async def generate(state):
        question = state["question"]
        documents = state["documents"]

        context = documents_to_context_str(documents)
        generation = await rag_chain.ainvoke({"context": context, "question": question})

        state["generation"] = generation
        return state

    async def grade_documents(state):
        question = state["question"]
        documents = state["documents"]

        relevant_docs = []
        for doc in documents:
            result = await filter_chain.ainvoke(
                {"document": doc.page_content, "question": question}
            )
            if result["score"]:
                relevant_docs.append(doc)

        state["documents"] = relevant_docs
        return state

    async def decide_to_generate_with_filtering(state):
        if len(state["documents"]) == 0:
            return "giveup"
        elif state["do_generate"]:
            return "generate"
        else:
            return "stop"

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


class RagWithRewritingChain(SimpleRagGraphState):
    remaining_rewrites: int


# flake8: noqa: C901
def rag_with_question_rewriting(
    llm: BaseLanguageModel, retriever: BaseRetriever, config: dict[str, Any]
) -> StateGraph:
    llm_type = config["llm_config"]["llm_type"]

    rag_prompt = get_rag_prompt(llm_type)
    rag_chain = rag_prompt | llm | StrOutputParser()

    filtering_prompt = get_docs_filtering_prompt(llm_type)
    filter_chain = filtering_prompt | llm | JsonOutputParser()

    rewrite_prompt = get_question_rewriting_prompt(llm_type)
    rewrite_chain = rewrite_prompt | llm | StrOutputParser()

    async def retrieve(state):
        question = state["question"]

        documents = await retriever.ainvoke(question)

        state["documents"] = documents
        return state

    async def generate(state):
        question = state["question"]
        documents = state["documents"]

        context = documents_to_context_str(documents)
        generation = await rag_chain.ainvoke({"context": context, "question": question})

        state["generation"] = generation
        return state

    async def rewrite(state):
        question = state["question"]

        generation = await rewrite_chain.ainvoke({"question": question})

        state["remaining_rewrites"] -= 1
        state["question"] = generation
        return state

    async def grade_documents(state):
        question = state["question"]
        documents = state["documents"]

        relevant_docs = []
        for doc in documents:
            result = await filter_chain.ainvoke(
                {"document": doc.page_content, "question": question}
            )
            if result["score"]:
                relevant_docs.append(doc)

        state["documents"] = relevant_docs
        return state

    async def decide_to_generate_with_filtering_and_rewriting(state):
        if len(state["documents"]) == 0:
            if state["remaining_rewrites"] > 0:
                return "rewrite"
            else:
                return "giveup"
        elif state["do_generate"]:
            return "generate"
        else:
            return "stop"

    workflow = StateGraph(RagWithRewritingChain)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("rewrite", rewrite)
    workflow.add_node("giveup", giveup)
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate_with_filtering_and_rewriting,
        {
            "giveup": "giveup",
            "generate": "generate",
            "rewrite": "rewrite",
            "stop": END,
        },
    )
    workflow.add_edge("giveup", END)
    workflow.add_edge("generate", END)

    return workflow
