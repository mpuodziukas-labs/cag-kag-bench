#!/usr/bin/env bash
# Offline verification: tests, bench, byte-identical rebuilds, lint. Prints GREEN.
# `--selftest` plants 4 defects plus 1 control and expects 5/5.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
cd "$here" || exit 1

if [ "${1:-}" = "--selftest" ]; then
  python3 scripts/selftest.py
  exit $?
fi

b="$here/build"
mkdir -p "$b"

# Every file under $1 must exist under $2 with identical bytes, and the counts must match.
same_tree() {
  local a="$1" c="$2" n=0 f
  while IFS= read -r f; do
    cmp -s "$a/$f" "$c/$f" || { echo "DIFF: $f ($a vs $c)" >&2; return 1; }
    n=$((n + 1))
  done < <(cd "$a" && find . -type f | sort)
  [ "$n" -gt 0 ] || { echo "no files compared in $a" >&2; return 1; }
  [ "$n" -eq "$(find "$c" -type f | wc -l | tr -d ' ')" ] || { echo "file count differs ($a vs $c)" >&2; return 1; }
  echo "byte-identical: $n files ($a vs $c)"
}

echo "== pytest"
python3 -m pytest -q

echo "== corpus built twice, and equal to the committed corpus"
python3 gen_corpus.py --out "$b/gen1"
python3 gen_corpus.py --out "$b/gen2"
same_tree "$b/gen1" "$b/gen2"
same_tree "$b/gen1/corpus" "$here/corpus"
cmp "$b/gen1/questions.jsonl" "$here/questions.jsonl"

echo "== bench run twice, and equal to the committed results"
python3 bench.py run --out "$b/run1"
python3 bench.py run --out "$b/run2" > /dev/null
same_tree "$b/run1" "$b/run2"
same_tree "$b/run1" "$here/results"
python3 bench.py readme --readme README.md --results results/RESULTS.md --check

echo "== prose lint"
if command -v dewatermark > /dev/null 2>&1; then
  for f in README.md results/RESULTS.md; do
    dewatermark --check "$f"
    dewatermark --check - < "$f"
  done
else
  echo "dewatermark not installed: skipped" >&2
fi

echo "== leak grep"
python3 scripts/leakcheck.py

echo "== shellcheck"
if command -v shellcheck > /dev/null 2>&1; then
  shellcheck "$here/scripts/verify.sh"
  echo "shellcheck rc 0"
else
  echo "shellcheck not installed: skipped" >&2
fi

echo "GREEN"
