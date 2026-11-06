import json

import gen_corpus
from common import load_corpus, load_questions
from kag.extract import extract_triples


def test_shape(docs, questions):
    assert len(docs) == 60
    assert len(questions) == 100
    assert sum(q["hops"] == 1 for q in questions) == 60
    assert sum(q["hops"] in (2, 3) for q in questions) == 40
    assert sum(q["split"] == "dev" for q in questions) == 50
    assert sum(q["split"] == "test" for q in questions) == 50
    assert len({q["question"] for q in questions}) == 100


def test_supporting_docs_exist_and_match_hop_count(docs, questions):
    for q in questions:
        assert len(q["support"]) == q["hops"]
        for d in q["support"]:
            assert d in docs and extract_triples(d, docs[d])


def test_generator_is_deterministic_and_matches_disk(docs, questions, tmp_path):
    d1, q1 = gen_corpus.build(gen_corpus.SEED)
    d2, q2 = gen_corpus.build(gen_corpus.SEED)
    assert (d1, q1) == (d2, q2)
    assert d1 == docs and q1 == questions
    gen_corpus.write(tmp_path, d1, q1)
    assert load_corpus(tmp_path / "corpus") == docs
    assert load_questions(tmp_path / "questions.jsonl") == questions
    assert json.loads((tmp_path / "questions.jsonl").read_text().splitlines()[0]) == questions[0]
