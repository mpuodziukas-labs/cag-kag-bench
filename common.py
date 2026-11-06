"""Shared types and loaders."""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edge:
    subj: str
    rel: str
    obj: str
    doc: str


@dataclass(frozen=True)
class Answer:
    text: str | None
    path: tuple = ()
    docs: tuple = ()
    ctx_tokens: int = 0
    reason: str = ""
    hit: bool = False


def count_tokens(text):
    """Token proxy used everywhere: whitespace-separated words."""
    return len(text.split())


def load_corpus(directory):
    return {p.stem: p.read_text().rstrip("\n") for p in sorted(Path(directory).glob("doc*.txt"))}


def load_questions(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]
