import os

from langchain_core.prompts import PromptTemplate


def get_rag_prompt(model_name: str) -> PromptTemplate:
    match model_name:
        case "gemma2_llama_cpp":
            return get_gemma2_rag_prompt()
        case _:
            raise ValueError("Unsupported model type")


def get_docs_filtering_prompt(model_name: str) -> PromptTemplate:
    match model_name:
        case "gemma2_llama_cpp":
            return get_gemma_docs_filtering_prompt()
        case _:
            raise ValueError("Unsupported model type")


def read_prompt_from_file(path: str) -> PromptTemplate:
    with open(path) as f:
        template = f.read().strip()

    prompt = PromptTemplate.from_template(template)
    return prompt


def get_gemma2_rag_prompt() -> PromptTemplate:
    template_path = os.path.join(
        os.path.dirname(__file__), "prompt_templates", "gemma2_rag.txt"
    )
    return read_prompt_from_file(template_path)


def get_gemma_docs_filtering_prompt() -> PromptTemplate:
    template_path = os.path.join(
        os.path.dirname(__file__), "prompt_templates", "gemma2_docs_filtering.txt"
    )
    return read_prompt_from_file(template_path)
