"""Knowledge graph with a multi-hop planner. Every answer carries its edge path."""
from common import Answer, count_tokens
from grammar import STEPS, parse_question
from kag.extract import extract_triples


class Graph:
    def __init__(self, edges):
        self._idx = {}
        for e in edges:
            self._idx.setdefault((e.rel, "out", e.subj), []).append(e)
            self._idx.setdefault((e.rel, "in", e.obj), []).append(e)

    def hop(self, cur, step):
        """One edge walk. Missing or ambiguous targets give None: never a guess."""
        rel, direction = STEPS[step]
        found = self._idx.get((rel, direction, cur), [])
        targets = {e.obj if direction == "out" else e.subj for e in found}
        if len(targets) != 1:
            return None
        return found[0], targets.pop()

    def walk(self, start, steps):
        cur, path = start, []
        for step in steps:
            res = self.hop(cur, step)
            if res is None:
                return None
            edge, cur = res
            path.append(edge)
        return tuple(path), cur


class KAG:
    def __init__(self, docs):
        self.docs = dict(docs)
        self.graph = Graph([e for d in sorted(docs) for e in extract_triples(d, docs[d])])

    def answer(self, question):
        parsed = parse_question(question)
        if parsed is None:
            return Answer(None, reason="unparseable question")
        steps, entity = parsed
        res = self.graph.walk(entity, steps)
        if res is None:
            return Answer(None, reason="no unique edge path")
        path, text = res
        for e in path:
            if e not in extract_triples(e.doc, self.docs.get(e.doc, "")):
                return Answer(None, reason=f"unsupported edge {e.subj} {e.rel} {e.obj}")
        docs = tuple(sorted({e.doc for e in path}))
        return Answer(text, path=path, docs=docs, ctx_tokens=sum(count_tokens(self.docs[d]) for d in docs))
