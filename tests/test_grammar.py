from common import Edge
from grammar import QUESTION_RX, TEMPLATES, parse_question
from kag.extract import extract_triples


def test_every_template_round_trips_and_matches_exactly_one():
    for fmt, steps in TEMPLATES:
        ent = "Ava Reyes" if steps[0] in ("led", "boss") else "Tidewell"
        q = fmt.format(e=ent)
        assert parse_question(q) == (steps, ent)
        assert sum(1 for rx, _ in QUESTION_RX if rx.fullmatch(q)) == 1


def test_parse_rejects_free_text():
    assert parse_question("What is the weather?") is None


def test_extract_triples_reads_only_grammar_sentences():
    text = "Wiki entry. The Tidewell team owns the Ledgerline system. Questions go to the usual channel."
    assert extract_triples("d1", text) == [Edge("Tidewell", "owns", "Ledgerline", "d1")]
    assert extract_triples("d2", "Ledgerline had a planned maintenance window last quarter.") == []
    assert extract_triples("d3", "Ava Reyes reports to Bo Lin.") == [Edge("Ava Reyes", "reports_to", "Bo Lin", "d3")]
