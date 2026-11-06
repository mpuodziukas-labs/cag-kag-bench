#!/usr/bin/env python3
"""Mutation selftest: plant defects in a scratch copy, the test suite must go red.

Each mutant must fail with pytest rc 1 (test failures, not a crash). The control
is a harmless edit and must stay green. Prints N/N and exits nonzero unless all pass.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "build" / "selftest"

MUTANTS = [
    ("stale cache entry served after a doc edit", "cag/cache.py",
     'return _sha(f"{normalize(question)}\\0{ctx_key}")',
     'return _sha(f"{normalize(question)}")', True),
    ("KAG answer emitted without provenance edge", "kag/graph.py",
     "return Answer(text, path=path, docs=docs,",
     "return Answer(text, path=(), docs=docs,", True),
    ("test split leaked into tuning", "bench.py",
     'dev = [q for q in questions if q["split"] == "dev"]',
     "dev = [q for q in questions if q['split'] in ('dev', 'test')]", True),
    ("BM25 idf sign flipped", "rag/bm25.py",
     "return math.log(1.0 + (n - df + 0.5) / (df + 0.5))",
     "return -math.log(1.0 + (n - df + 0.5) / (df + 0.5))", True),
    ("control: comment-only edit stays green", "rag/bm25.py",
     "# Okapi BM25 with the non-negative log(1 + x) idf.",
     "# Okapi BM25, non-negative idf variant.", False),
]


def run_one(i, name, rel, old, new, must_fail):
    work = SCRATCH / f"case{i}"
    shutil.copytree(ROOT, work, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("build", ".verify", "__pycache__", ".pytest_cache", ".git"))
    target = work / rel
    src = target.read_text()
    if src.count(old) != 1:
        return False, f"patch anchor found {src.count(old)} times in {rel}"
    target.write_text(src.replace(old, new))
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"],
                       cwd=work, capture_output=True, text=True)
    ok = (r.returncode == 1) if must_fail else (r.returncode == 0)
    return ok, f"pytest rc {r.returncode}"


def main():
    passed = 0
    for i, case in enumerate(MUTANTS, 1):
        ok, detail = run_one(i, *case)
        print(f"{'PASS' if ok else 'FAIL'}  {case[0]} ({detail})")
        passed += ok
    print(f"selftest {passed}/{len(MUTANTS)}")
    return 0 if passed == len(MUTANTS) and len(MUTANTS) == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
