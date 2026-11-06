"""Plain retrieval-augmented answering: BM25 top-k, answerer reads only those docs."""
from dataclasses import replace

from common import count_tokens
from rag.bm25 import BM25


class RAG:
    def __init__(self, docs, answerer, k1=1.2, b=0.75, top_k=3):
        self.docs, self.answerer, self.top_k = dict(docs), answerer, top_k
        self.bm25 = BM25(self.docs, k1, b)

    def answer(self, question):
        ids = self.bm25.top(question, self.top_k)
        ans = self.answerer.answer(question, [(i, self.docs[i]) for i in ids])
        return replace(ans, docs=tuple(ids), ctx_tokens=sum(count_tokens(self.docs[i]) for i in ids))
