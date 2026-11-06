from dataclasses import replace

from kag.graph import KAG


def test_every_answer_is_gold_and_carries_a_full_provenance_path(docs, questions):
    kag = KAG(docs)
    for q in questions:
        a = kag.answer(q["question"])
        assert a.text == q["answer"], q["id"]
        assert len(a.path) == q["hops"], q["id"]
        assert {e.doc for e in a.path} == set(q["support"]), q["id"]


def test_unsupported_edge_is_refused_never_guessed(docs, questions):
    kag = KAG(docs)
    q = next(x for x in questions if x["hops"] == 2)
    victim = kag.answer(q["question"]).path[0].doc
    kag.docs = {**docs, victim: "Wiki entry. Nothing to see here."}
    a = kag.answer(q["question"])
    assert a.text is None and "unsupported" in a.reason


def test_unknown_entity_and_free_text_are_refused(docs):
    kag = KAG(docs)
    assert kag.answer("Who leads the Zzyzx team?").text is None
    assert kag.answer("What is the weather?").text is None


def test_ambiguous_edges_are_refused():
    docs = {"a": "Ava Reyes reports to Bo Lin.", "b": "Ava Reyes reports to Cy Dow."}
    assert KAG(docs).answer("Who does Ava Reyes report to?").text is None
