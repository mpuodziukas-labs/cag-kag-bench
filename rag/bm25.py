"""BM25 retriever, stdlib only."""
import math
import re
from collections import Counter


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        self.k1, self.b = k1, b
        self.ids = sorted(docs)
        self.tf = {i: Counter(tokenize(docs[i])) for i in self.ids}
        self.len = {i: sum(self.tf[i].values()) for i in self.ids}
        self.avg = sum(self.len.values()) / len(self.ids)
        self.df = Counter()
        for tf in self.tf.values():
            self.df.update(tf.keys())

    def idf(self, term):
        # Okapi BM25 with the non-negative log(1 + x) idf.
        n, df = len(self.ids), self.df.get(term, 0)
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def top(self, query, k):
        terms = tokenize(query)
        scored = []
        for i in self.ids:
            norm = self.k1 * (1 - self.b + self.b * self.len[i] / self.avg)
            s = sum(self.idf(t) * self.tf[i][t] * (self.k1 + 1) / (self.tf[i][t] + norm) for t in terms if t in self.tf[i])
            if s > 0:
                scored.append((-s, i))
        scored.sort()
        return [i for _, i in scored[:k]]
