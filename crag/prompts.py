import os

from langchain_core.prompts import PromptTemplate


def get_rag_prompt(model_name: str) -> PromptTemplate:
    match model_name:
        case "gemma2_llama_cpp":
            return get_gemma2_rag_prompt()
        case _:
            raise ValueError("Unsupported model type")


def get_gemma2_rag_prompt() -> PromptTemplate:
    dir_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(dir_path, "prompt_templates", "gemma2_rag.txt")
    with open(template_path) as f:
        template = f.read().strip()

    prompt = PromptTemplate.from_template(template)
    return prompt
