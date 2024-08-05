import json
import os
import re
from typing import Any, List

from langchain_core.documents import Document


def make_html_link(url: str, name: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def docs_to_sources_str(documents: List[Document]) -> str:
    links = set()
    source_text_rows = []
    for doc in documents:
        title = doc.metadata["title"]

        if "is_public" in doc.metadata and not doc.metadata["is_public"]:
            link = doc.metadata.get("public_source", None)
        else:
            link = doc.metadata["source"]

        author = doc.metadata.get("author", None)

        if link is not None:
            if link in links:
                continue
            links.add(link)
            citation = make_html_link(link, title)
            if author is not None:
                citation += f" від {author}"
        else:
            citation = title + f" від {author}:" + "\n\n" + doc.page_content + "\n"

        idx = len(source_text_rows) + 1
        out_row = f"[{idx}] {citation}"
        source_text_rows.append(out_row)

    sources_text = "\n".join(source_text_rows)
    return sources_text


def recursive_substitute_envs(cfg: dict[str, Any]) -> None:
    for k, v in cfg.items():
        if isinstance(v, dict):
            recursive_substitute_envs(v)
        elif isinstance(v, str):
            prev_end = 0
            new_value = ""
            for match in re.finditer("{env.\w+}", v):  # noqa
                env_name = match.group()[5:-1]
                new_value += v[prev_end : match.start()] + os.getenv(env_name)
                prev_end = match.end()
            if prev_end != 0:
                cfg[k] = new_value


def load_config() -> dict[str, Any]:
    cfg_path = "config.json"
    with open(cfg_path) as file:
        cfg = json.load(file)

    recursive_substitute_envs(cfg)

    return cfg
