from typing import List, Sequence

from langchain.retrievers import (
    ParentDocumentRetriever as LangchainParentDocumentRetriever,
)
from langchain_core.documents import Document
from langchain_core.stores import BaseStore
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import TextSplitter

from crag.retrievers.base import PipelineRetrieverBase


class ParentDocumentRetriever(PipelineRetrieverBase, LangchainParentDocumentRetriever):
    """ParentDocumentRetriever entended with ability to cascade delete documents"""

    def __init__(
        self,
        vector_store: VectorStore,
        docstore: BaseStore[str, Document],
        child_splitter: TextSplitter,
        parent_splitter: TextSplitter | None = None,
        child_metadata_fields: Sequence[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            vectorstore=vector_store,
            docstore=docstore,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
            child_metadata_fields=child_metadata_fields,
            **kwargs,
        )

    @property
    def retriever(self):
        return self

    async def aadd_documents(
        self,
        docs: List[Document],
        ids: List[str] | None = None,
        **kwargs,
    ) -> List[str]:
        docs, full_docs = self._split_docs_for_adding(docs, ids, True)
        children_ids = await self.vectorstore.aadd_documents(docs, **kwargs)

        for _, full_doc in full_docs:
            full_doc.metadata["children_ids"] = []

        curr_parent_idx = 0
        for child_id, doc in zip(children_ids, docs):
            parent_id = doc.metadata[self.id_key]
            # child docs are sorted by parente docs
            for id, full_doc in full_docs[curr_parent_idx:]:
                if id == parent_id:
                    full_doc.metadata["children_ids"].append(child_id)
                else:
                    curr_parent_idx += 1
                    break

        await self.docstore.amset(full_docs)
        return list(id for id, _ in full_docs)

    async def adelete_documents(self, ids: List[str]) -> bool | None:
        for docs in await self.docstore.amget(ids):
            children_ids = docs.metadata["children_ids"]
            await self.vectorstore.adelete(children_ids)

        await self.docstore.amdelete(ids)

        return True
