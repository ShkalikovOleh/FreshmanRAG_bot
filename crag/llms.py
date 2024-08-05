import os
from typing import Any

from langchain.base_language import BaseLanguageModel


def get_llm(model_config: dict[str, Any]) -> BaseLanguageModel:
    type = model_config["llm_type"]
    args = model_config["llm_args"]

    match type:
        case "gemma2_llama_cpp":
            return get_llama_cpp(**args)
        case _:
            raise ValueError("Unsupported model type")


def get_llama_cpp(**kwargs) -> BaseLanguageModel:
    from langchain_community.llms import LlamaCpp

    model_path = os.path.abspath(kwargs.pop("model_path"))
    llm = LlamaCpp(**kwargs, model_path=model_path, verbose=False)
    return llm
