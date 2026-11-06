import cag.cache as cache
from answerer import ExtractiveStub
from cag.cache import CAG, context_key, pack

DOCS = {
    "d1": "Ava Reyes reports to Bo Lin.",
    "d2": "Cy Dow reports to Ava Reyes.",
}
Q = "Who does Ava Reyes report to?"


def test_context_key_tracks_content_and_packer_version(monkeypatch):
    k = context_key(DOCS, 100)
    assert k == context_key(dict(DOCS), 100)
    assert k != context_key({**DOCS, "d1": "Ava Reyes reports to Dee Fox."}, 100)
    monkeypatch.setattr(cache, "PACKER_VERSION", "pack-v2")
    assert k != context_key(DOCS, 100)


def test_pack_respects_budget():
    ctx, used = pack(DOCS, 1000)
    assert [d for d, _ in ctx] == ["d1", "d2"] and used <= 1000
    ctx, used = pack(DOCS, 7)
    assert [d for d, _ in ctx] == ["d1"] and used <= 7


def test_hit_miss_and_normalized_question():
    c = CAG(DOCS, ExtractiveStub())
    a = c.answer(Q)
    assert a.text == "Bo Lin" and not a.hit
    b = c.answer("  who does AVA reyes report to  ")
    assert b.text == "Bo Lin" and b.hit
    assert (c.hits, c.misses) == (1, 1)


def test_stale_entry_is_never_served_after_a_doc_edit():
    c = CAG(DOCS, ExtractiveStub())
    assert c.answer(Q).text == "Bo Lin"
    old = c.key
    c.update_doc("d1", "Ava Reyes reports to Dee Fox.")
    assert c.key != old
    a = c.answer(Q)
    assert a.text == "Dee Fox" and not a.hit
