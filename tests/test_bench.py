import json

import bench
from answerer import ExtractiveStub


class Poison(dict):
    """A question that may only be asked which split it is in."""

    def __getitem__(self, key):
        if key != "split":
            raise AssertionError("tuning touched a non-dev question")
        return super().__getitem__(key)


def test_wilson_known_values():
    lo, hi = bench.wilson(50, 100)
    assert round(lo, 4) == 0.4038 and round(hi, 4) == 0.5962
    assert bench.wilson(0, 10)[0] == 0.0
    assert round(bench.wilson(10, 10)[1], 6) == 1.0


def test_tuning_never_reads_the_test_split(docs, questions):
    mixed = [q if q["split"] == "dev" else Poison(q) for q in questions]
    params, em, n = bench.tune(docs, mixed, ExtractiveStub(), bench.load_params(bench.ROOT)["grid"])
    assert n == 50 and 0 <= em <= n and params["top_k"] >= 1


def test_run_is_deterministic_and_reports_test_split_only(tmp_path):
    bench.run(bench.ROOT, tmp_path / "a", quiet=True)
    bench.run(bench.ROOT, tmp_path / "b", quiet=True)
    for name in ("results.json", "RESULTS.md"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    res = json.loads((tmp_path / "a" / "results.json").read_text())
    assert res["config"]["n_test"] == 50
    for m in ("rag", "cag", "kag"):
        assert res["methods"][m]["overall"]["n"] == 50
    assert res["methods"]["cag"]["cache"]["warm_pass_identical"] is True
    assert res["methods"]["cag"]["cache"]["warm_hit_rate"] == 1.0


def test_readme_sync_is_idempotent_and_replaces_only_the_block():
    text = "intro\n<!-- RESULTS:BEGIN -->\nold\n<!-- RESULTS:END -->\noutro\n"
    once = bench.sync_readme(text, "NEW\n")
    assert once == "intro\n<!-- RESULTS:BEGIN -->\nNEW\n<!-- RESULTS:END -->\noutro\n"
    assert bench.sync_readme(once, "NEW\n") == once
