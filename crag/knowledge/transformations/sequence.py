from typing import Callable, List, Tuple, Union

from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter


class TransformationSequence:
    def __init__(
        self,
        transforms: List[
            Tuple[str, Union[Callable[[List[Document]], List[Document]], TextSplitter]]
        ],
    ) -> None:
        self.transforms = transforms

    def apply(self, docs: List[Document]) -> List[Document]:
        for type, trans in self.transforms:
            match type:
                case "function":
                    docs = trans(docs)
                case "text_splitter":
                    docs = trans.split_documents(docs)
                case _:
                    continue

        return docs
