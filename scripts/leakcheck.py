#!/usr/bin/env python3
"""Leak grep: vendor or model names, home paths, IP literals, em dashes. Fails on any hit."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"build", ".verify", "__pycache__", ".pytest_cache", ".git"}
# Patterns are assembled from pieces so this file does not match itself.
PATTERNS = {
    "vendor or model name": re.compile("(" + "|".join(["anthro" + "pic", "open" + "ai", "clau" + "de", "gp" + "t", "gem" + "ini", "lla" + "ma", "mist" + "ral"]) + ")", re.I),
    "home path": re.compile("(/Us" + "ers/|/ho" + "me/|" + chr(126) + "/)"),
    "ip literal": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "em dash": re.compile(chr(0x2014)),
}


def main():
    files = [p for p in ROOT.rglob("*") if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS)]
    if not files:
        print("leakcheck: no files scanned", file=sys.stderr)
        return 1
    hits = 0
    for p in sorted(files):
        try:
            text = p.read_text()
        except UnicodeDecodeError:
            continue
        for label, rx in PATTERNS.items():
            for m in rx.finditer(text):
                print(f"LEAK {label}: {p.relative_to(ROOT)}: {m.group(0)!r}")
                hits += 1
    print(f"leakcheck: {len(files)} files scanned, {hits} hits")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
