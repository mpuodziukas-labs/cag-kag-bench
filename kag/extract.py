"""Rule-based triple extractor over the synthetic doc grammar."""
import re

from common import Edge
from grammar import FACT_RX


def extract_triples(doc_id, text):
    edges = []
    for sentence in re.split(r"(?<=\.)\s+", text.strip()):
        for rel, rx in FACT_RX.items():
            m = rx.fullmatch(sentence)
            if m:
                edges.append(Edge(m["a"], rel, m["b"], doc_id))
                break
    return edges
