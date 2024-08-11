from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, START, StateGraph

from crag.pipelines.base import SimpleRagGraphState, giveup
from crag.pipelines.rag_with_docs_filtering import RAGWithDocsFiltering
from crag.retrievers.base import PipelineRetrieverBase


class RAGWithQuestionRewritingState(SimpleRagGraphState):
    remaining_rewrites: int


class RAGWithQuestionRewriting(RAGWithDocsFiltering):

    def __init__(
        self,
        retriever: PipelineRetrieverBase,
        llm: BaseLanguageModel,
        rag_prompt: PromptTemplate,
        gradining_prompt: PromptTemplate,
        rewriting_prompt: PromptTemplate,
    ) -> None:
        super().__init__(retriever, llm, rag_prompt, gradining_prompt)
        self._rewrite_chain = rewriting_prompt | llm | StrOutputParser()

    async def rewrite(
        self, state: RAGWithQuestionRewritingState
    ) -> RAGWithQuestionRewritingState:
        question = state["question"]

        generation = await self._rewrite_chain.ainvoke({"question": question})

        state["remaining_rewrites"] -= 1
        state["question"] = generation
        return state

    async def decide_to_generate(self, state: RAGWithQuestionRewritingState) -> str:
        if len(state["documents"]) == 0:
            if state["remaining_rewrites"] > 0:
                return "rewrite"
            else:
                return "giveup"
        elif state["do_generate"]:
            return "generate"
        else:
            return "stop"

    def construct_graph(self) -> StateGraph:
        workflow = StateGraph(RAGWithQuestionRewritingState)

        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("rewrite", self.rewrite)
        workflow.add_node("giveup", giveup)
        workflow.add_node("generate", self.generate)

        workflow.add_edge(START, "retrieve")
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
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
