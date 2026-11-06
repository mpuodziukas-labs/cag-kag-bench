from answerer import ExtractiveStub
from rag.bm25 import BM25
from rag.pipeline import RAG

DOCS = {
    "d1": "apple banana",
    "d2": "apple cherry",
    "d3": "apple durian",
    "d4": "elder fig",
}


def test_rare_term_has_higher_idf_and_idf_is_positive():
    bm = BM25(DOCS)
    assert bm.idf("banana") > bm.idf("apple") > 0
    assert bm.idf("never-seen") > 0


def test_ranking_prefers_the_doc_with_the_rare_term_and_ties_break_by_id():
    bm = BM25(DOCS)
    assert bm.top("apple banana", 3)[0] == "d1"
    assert bm.top("apple", 3) == ["d1", "d2", "d3"]
    assert bm.top("zzz", 3) == []


def test_answerer_sees_only_retrieved_text():
    docs = {
        "d1": "Ava Reyes reports to Bo Lin.",
        "d2": "Cy Dow reports to Ava Reyes.",
        "d3": "Ava Reyes reports to Bo Lin. Ava Reyes reports to Bo Lin.",
    }
    full = RAG(docs, ExtractiveStub(), top_k=3).answer("Who does Cy Dow report to?")
    assert full.text == "Ava Reyes"
    miss = RAG(docs, ExtractiveStub(), top_k=1).answer("Who does Cy Dow report to?")
    assert miss.docs == ("d2",) and miss.text == "Ava Reyes"
    none = RAG(docs, ExtractiveStub(), top_k=1).answer("Which team does Cy Dow lead?")
    assert none.text is None
