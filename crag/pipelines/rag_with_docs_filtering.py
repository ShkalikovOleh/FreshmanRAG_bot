from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, START, StateGraph

from crag.pipelines.base import SimpleRagGraphState, giveup
from crag.pipelines.simple_rag import SimpleRAG
from crag.retrievers.base import PipelineRetrieverBase


class RAGWithDocsFiltering(SimpleRAG):

    def __init__(
        self,
        retriever: PipelineRetrieverBase,
        llm: BaseLanguageModel,
        rag_prompt: PromptTemplate,
        gradining_prompt: PromptTemplate,
    ) -> None:
        super().__init__(retriever, llm, rag_prompt)
        self._grade_chain = gradining_prompt | llm | JsonOutputParser()

    async def grade_documents(self, state: SimpleRagGraphState) -> SimpleRagGraphState:
        question = state["question"]
        documents = state["documents"]

        relevant_docs = []
        for doc in documents:
            result = await self._grade_chain.ainvoke(
                {"document": doc.page_content, "question": question}
            )
            if result["score"]:
                relevant_docs.append(doc)

        state["documents"] = relevant_docs
        return state

    async def decide_to_generate(self, state: SimpleRagGraphState) -> str:
        if len(state["documents"]) == 0:
            return "giveup"
        elif state["do_generate"]:
            return "generate"
        else:
            return "stop"

    def construct_graph(self) -> StateGraph:
        workflow = StateGraph(SimpleRagGraphState)

        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("giveup", giveup)
        workflow.add_node("generate", self.generate)

        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "giveup": "giveup",
                "generate": "generate",
                "stop": END,
            },
        )
        workflow.add_edge("giveup", END)
        workflow.add_edge("generate", END)

        return workflow
