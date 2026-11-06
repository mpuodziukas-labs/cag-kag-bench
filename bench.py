#!/usr/bin/env python3
"""RAG vs CAG vs KAG on the synthetic corpus. Reports the test split only.

  python3 bench.py run [--out DIR]
  python3 bench.py readme --readme README.md --results results/RESULTS.md [--check]
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import yaml

from answerer import ExtractiveStub
from cag.cache import CAG
from common import load_corpus, load_questions
from kag.graph import KAG
from rag.pipeline import RAG

ROOT = Path(__file__).resolve().parent
BEGIN, END = "<!-- RESULTS:BEGIN -->", "<!-- RESULTS:END -->"


def load_params(root):
    return yaml.safe_load((Path(root) / "params.yaml").read_text())


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - spread) / denom), min(1.0, (centre + spread) / denom)


def exact(pred, gold):
    return pred is not None and pred.strip().lower() == gold.strip().lower()


def tune(docs, questions, answerer, grid):
    """Pick RAG parameters by exact match on the dev split. Ties keep the earlier grid cell."""
    dev = [q for q in questions if q["split"] == "dev"]
    best = None
    for top_k in grid["top_k"]:
        for k1 in grid["k1"]:
            for b in grid["b"]:
                rag = RAG(docs, answerer, k1=k1, b=b, top_k=top_k)
                em = sum(exact(rag.answer(q["question"]).text, q["answer"]) for q in dev)
                if best is None or em > best[0]:
                    best = (em, {"top_k": top_k, "k1": k1, "b": b})
    return best[1], best[0], len(dev)


def evaluate(method, questions, timings, label):
    recs = []
    for q in questions:
        t0 = time.perf_counter()
        a = method.answer(q["question"])
        timings.setdefault(label, []).append(time.perf_counter() - t0)
        gold = set(q["support"])
        recs.append({
            "hops": q["hops"],
            "em": exact(a.text, q["answer"]),
            "refused": a.text is None,
            "recall": len(gold & set(a.docs)) / len(gold),
            "ctx": a.ctx_tokens,
            "text": a.text,
        })
    return recs


def interval(recs):
    k, n = sum(r["em"] for r in recs), len(recs)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "acc": round(k / n, 4), "lo": round(lo, 4), "hi": round(hi, 4)}


def summarize(recs):
    return {
        "overall": interval(recs),
        "single": interval([r for r in recs if r["hops"] == 1]),
        "multi": interval([r for r in recs if r["hops"] > 1]),
        "by_hops": {str(h): interval([r for r in recs if r["hops"] == h]) for h in (1, 2, 3)},
        "support_recall": round(sum(r["recall"] for r in recs) / len(recs), 4),
        "mean_context_tokens": round(sum(r["ctx"] for r in recs) / len(recs), 1),
        "refused": sum(r["refused"] for r in recs),
    }


def compare(group, m):
    a, b = m["kag"][group], m["rag"][group]
    order = "KAG higher" if a["acc"] > b["acc"] else "RAG higher" if a["acc"] < b["acc"] else "equal"
    overlap = a["lo"] <= b["hi"] and b["lo"] <= a["hi"]
    return (
        f"{group}-hop test: KAG {a['acc']:.4f} vs RAG {b['acc']:.4f}; {order}; "
        f"95% intervals {'overlap' if overlap else 'do not overlap'}.", a["acc"] > b["acc"], overlap)


def claims(m):
    multi, kag_wins, _ = compare("multi", m)
    single, _, overlap = compare("single", m)
    return [
        multi,
        single,
        f"Expected KAG above RAG on multi-hop: {'HELD' if kag_wins else 'DID NOT HOLD'}.",
        f"Expected RAG matching KAG on single-hop (intervals overlap): {'HELD' if overlap else 'DID NOT HOLD'}.",
    ]


def cell(s):
    return f"{s['acc']:.4f} [{s['lo']:.4f}, {s['hi']:.4f}] ({s['k']}/{s['n']})"


def render(res):
    m, cfg, tu = res["methods"], res["config"], res["dev_tuning"]
    rows = ["| method | overall | single-hop | multi-hop | 1-hop | 2-hop | 3-hop |", "|---|---|---|---|---|---|---|"]
    for name in ("rag", "cag", "kag"):
        s = m[name]
        rows.append(f"| {name.upper()} | " + " | ".join(
            [cell(s["overall"]), cell(s["single"]), cell(s["multi"])] + [cell(s["by_hops"][h]) for h in "123"]) + " |")
    ev = ["| method | supporting-doc recall | mean context tokens | refused |", "|---|---|---|---|"]
    for name in ("rag", "cag", "kag"):
        s = m[name]
        ev.append(f"| {name.upper()} | {s['support_recall']:.4f} | {s['mean_context_tokens']:.1f} | {s['refused']} |")
    c = m["cag"]["cache"]
    return "\n".join([
        "### Test-split results",
        "",
        f"Corpus: {cfg['n_docs']} docs. Questions: {cfg['n_dev']} dev, {cfg['n_test']} test (seeded 50/50 split). "
        f"Only the {cfg['n_test']} test questions are reported. "
        f"RAG parameters were tuned on dev only: top_k={tu['best']['top_k']}, k1={tu['best']['k1']}, b={tu['best']['b']} "
        f"(dev exact match {tu['dev_em']['k']}/{tu['dev_em']['n']}).",
        "",
        "Exact match, with Wilson 95% intervals in brackets:",
        "",
        *rows,
        "",
        "Evidence: supporting-doc recall is the share of gold supporting docs the method surfaced to its answerer "
        "(RAG: retrieved docs; CAG: docs packed into the context; KAG: docs behind the edges it walked).",
        "",
        *ev,
        "",
        f"CAG context budget {cfg['context_budget_tokens']} whitespace tokens, {cfg['cag_docs_packed']} of {cfg['n_docs']} docs packed. "
        f"Answer cache hit rate: cold pass {c['cold_hit_rate']:.4f}, warm pass {c['warm_hit_rate']:.4f}, "
        f"overall {c['overall_hit_rate']:.4f}. Per-query wall time is printed by bench.py and not stored, because it is not deterministic.",
        "",
        "What the numbers say:",
        "",
        *[f"- {x}" for x in res["claims"]],
        "",
    ])


def run(root, out, quiet=False):
    root, out = Path(root), Path(out)
    params = load_params(root)
    docs = load_corpus(root / "corpus")
    questions = load_questions(root / "questions.jsonl")
    stub = ExtractiveStub()
    best, dev_k, dev_n = tune(docs, questions, stub, params["grid"])
    test = [q for q in questions if q["split"] == "test"]
    timings = {}

    rag = RAG(docs, stub, **best)
    cag = CAG(docs, stub, budget=params["context_budget_tokens"])
    kag = KAG(docs)
    r_rag = evaluate(rag, test, timings, "rag")
    r_cold = evaluate(cag, test, timings, "cag cold")
    cold_hits = cag.hits
    r_warm = evaluate(cag, test, timings, "cag warm")
    r_kag = evaluate(kag, test, timings, "kag")

    methods = {"rag": summarize(r_rag), "cag": summarize(r_cold), "kag": summarize(r_kag)}
    n = len(test)
    methods["cag"]["cache"] = {
        "cold_hit_rate": round(cold_hits / n, 4),
        "warm_hit_rate": round((cag.hits - cold_hits) / n, 4),
        "overall_hit_rate": round(cag.hits / (cag.hits + cag.misses), 4),
        "warm_pass_identical": [r["text"] for r in r_warm] == [r["text"] for r in r_cold],
    }
    res = {
        "config": {
            "n_docs": len(docs), "n_dev": len(questions) - n, "n_test": n,
            "context_budget_tokens": params["context_budget_tokens"], "cag_docs_packed": len(cag.context),
            "token_proxy": "whitespace",
        },
        "dev_tuning": {"best": best, "dev_em": {"k": dev_k, "n": dev_n}},
        "methods": methods,
    }
    res["claims"] = claims(methods)

    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(res, sort_keys=True, indent=2) + "\n")
    (out / "RESULTS.md").write_text(render(res))
    if not quiet:
        print((out / "RESULTS.md").read_text())
        print("per-query wall time, mean ms (printed only, not stored):")
        for label in sorted(timings):
            print(f"  {label:10s} {1000 * sum(timings[label]) / len(timings[label]):.3f}")
    return res


def sync_readme(text, block):
    if BEGIN not in text or END not in text:
        raise ValueError("README is missing the RESULTS markers")
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    return f"{head}{BEGIN}\n{block}{END}{tail}"


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", default=str(ROOT / "results"))
    d = sub.add_parser("readme")
    d.add_argument("--readme", required=True)
    d.add_argument("--results", required=True)
    d.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(ROOT, a.out)
        return 0
    readme, block = Path(a.readme), Path(a.results).read_text()
    new = sync_readme(readme.read_text(), block)
    if a.check:
        if new != readme.read_text():
            print("README results block is out of sync with RESULTS.md", file=sys.stderr)
            return 1
        print("README results block in sync")
        return 0
    readme.write_text(new)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
