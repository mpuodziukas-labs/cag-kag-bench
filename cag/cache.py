"""Cache-augmented generation: whole corpus preloaded once, exact-match answer cache."""
import hashlib
from dataclasses import replace

from common import count_tokens
from grammar import normalize

PACKER_VERSION = "pack-v1"
DEFAULT_BUDGET = 4000  # whitespace-token proxy


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def pack(docs, budget):
    """Pack docs in id order until the next one would overflow the budget."""
    ctx, used = [], 0
    for i in sorted(docs):
        n = count_tokens(f"[{i}] {docs[i]}")
        if used + n > budget:
            break
        ctx.append((i, docs[i]))
        used += n
    return ctx, used


def context_key(docs, budget):
    blob = "\n".join(f"{i}\t{docs[i]}" for i in sorted(docs))
    return _sha(f"{blob}\0{PACKER_VERSION}:budget={budget}")


def answer_key(question, ctx_key):
    return _sha(f"{normalize(question)}\0{ctx_key}")


class CAG:
    def __init__(self, docs, answerer, budget=DEFAULT_BUDGET):
        self.docs, self.answerer, self.budget = dict(docs), answerer, budget
        self._cache, self.hits, self.misses = {}, 0, 0
        self._load()

    def _load(self):
        self.context, self.ctx_tokens = pack(self.docs, self.budget)
        self.key = context_key(self.docs, self.budget)

    def update_doc(self, doc_id, text):
        """Any source change moves the context key, so older answers can no longer match."""
        self.docs[doc_id] = text
        self._load()

    def answer(self, question):
        k = answer_key(question, self.key)
        if k in self._cache:
            self.hits += 1
            return replace(self._cache[k], hit=True)
        self.misses += 1
        ans = self.answerer.answer(question, self.context)
        ans = replace(ans, docs=tuple(i for i, _ in self.context), ctx_tokens=self.ctx_tokens)
        self._cache[k] = ans
        return ans
