"""Answerer interface and a deterministic extractive stub (no model, no network)."""
from typing import Protocol

from common import Answer
from grammar import parse_question
from kag.extract import extract_triples
from kag.graph import Graph


class Answerer(Protocol):
    def answer(self, question: str, context: list) -> Answer:
        """context is a list of (doc_id, text); read nothing else."""


class ExtractiveStub:
    """Reads only the context it is handed. Chains facts found there; else abstains."""

    def answer(self, question, context):
        parsed = parse_question(question)
        if parsed is None:
            return Answer(None, reason="unparseable question")
        steps, entity = parsed
        edges = [e for d, t in context for e in extract_triples(d, t)]
        res = Graph(edges).walk(entity, steps)
        if res is None:
            return Answer(None, reason="evidence not in context")
        path, text = res
        return Answer(text, path=path)
