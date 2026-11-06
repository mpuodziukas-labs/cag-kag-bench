#!/usr/bin/env python3
"""Seeded generator for the fictional-company corpus and the question set.

Gold answers come from plain dict lookups on the world model, not from the
graph code under test.
"""
import argparse
import json
import random
from pathlib import Path

from grammar import FACT_FORMATS, START_KIND, TEMPLATES

SEED = 20261105
N_TEAMS, N_SYSTEMS, N_PEOPLE, N_DEPS, N_DISTRACTORS = 10, 16, 16, 11, 8
QUOTA_2HOP, QUOTA_3HOP = 22, 18

FIRST = ["Ava", "Bo", "Cy", "Dee", "Eli", "Fay", "Gus", "Hana", "Ivo", "Jun", "Kit", "Lena", "Moe", "Nia", "Oto", "Pia", "Quin", "Rae"]
LAST = ["Reyes", "Lin", "Dow", "Fox", "Kim", "Ward", "Shaw", "Vale", "Hart", "Penn", "Cole", "Stone", "Bright", "Marsh", "Lowe", "Park", "Frost", "Nash"]
TEAMS = ["Tidewell", "Ashcombe", "Brindle", "Copperfen", "Dunmere", "Elmhollow", "Fallowmoor", "Grayholt", "Harrowgate", "Ironwick", "Juniperlane", "Kestrelby"]
SYSTEMS = ["Ledgerline", "Brightqueue", "Tallyforge", "Mossbridge", "Quillstream", "Rivetmap", "Sablegate", "Thornvault", "Umberdesk", "Vellumhub", "Wickerpath", "Yarrowgrid", "Zephyrlog", "Amberrelay", "Basaltcore", "Cinderpost", "Dovetailer", "Emberindex"]
LEADINS = ["Wiki entry.", "Handbook note.", "Internal page.", "Directory record.", "Team index.", "Reference card."]
FILLERS = [
    "Questions go to the usual channel.",
    "This page is reviewed once a quarter.",
    "See the runbook for escalation steps.",
    "Updates are announced at the weekly sync.",
    "Older versions are kept in the archive.",
    "Contact details are listed on the intranet.",
    "Changes need a short written rationale.",
    "The page owner keeps a changelog.",
]
DISTRACTORS = [
    "{S} had a planned maintenance window last quarter.",
    "A review of the {T} team is planned for next spring.",
    "{P} gave a talk at the all-hands meeting.",
]


def build(seed):
    rng = random.Random(seed)
    names = [f"{f} {l}" for f in FIRST for l in LAST]
    people = rng.sample(names, N_PEOPLE)
    teams = rng.sample(TEAMS, N_TEAMS)
    systems = rng.sample(SYSTEMS, N_SYSTEMS)

    owner = {s: (teams[i] if i < N_TEAMS else rng.choice(teams)) for i, s in enumerate(systems)}
    lead = dict(zip(teams, rng.sample(people, N_TEAMS)))
    led = {p: t for t, p in lead.items()}
    boss = {people[i]: people[rng.randrange(max(0, i - 3), i)] for i in range(1, N_PEOPLE)}
    dep = {systems[i]: systems[rng.randrange(max(0, i - 3), i)] for i in rng.sample(range(1, N_SYSTEMS), N_DEPS)}
    world = {"owner": owner, "lead": lead, "led": led, "boss": boss, "dep": dep}

    facts = (
        [("owns", t, s) for s, t in owner.items()]
        + [("leads", p, t) for t, p in lead.items()]
        + [("reports_to", a, b) for a, b in boss.items()]
        + [("depends_on", a, b) for a, b in dep.items()]
    )
    distractors = [
        DISTRACTORS[i % 3].format(S=rng.choice(systems), T=rng.choice(teams), P=rng.choice(people))
        for i in range(N_DISTRACTORS)
    ]
    bodies = [("fact", f) for f in facts] + [("memo", d) for d in distractors]
    rng.shuffle(bodies)

    docs, fact_doc = {}, {}
    for n, (kind, body) in enumerate(bodies, 1):
        doc_id = f"doc{n:03d}"
        if kind == "fact":
            rel, a, b = body
            sentence = FACT_FORMATS[rel].format(a=a, b=b)
            fact_doc[(rel, a, b)] = doc_id
        else:
            sentence = body
        docs[doc_id] = " ".join([rng.choice(LEADINS), sentence, rng.choice(FILLERS)])

    kinds = {"system": systems, "team": teams, "person": people}
    step_fact = {  # step -> fact tuple from the current entity and the step result
        "owner": lambda cur, nxt: ("owns", nxt, cur),
        "lead": lambda cur, nxt: ("leads", nxt, cur),
        "led": lambda cur, nxt: ("leads", cur, nxt),
        "boss": lambda cur, nxt: ("reports_to", cur, nxt),
        "dep": lambda cur, nxt: ("depends_on", cur, nxt),
    }
    pools = {}
    for fmt, steps in TEMPLATES:
        for e in kinds[START_KIND[steps[0]]]:
            cur, support = e, []
            for st in steps:
                nxt = world[st].get(cur)
                if nxt is None:
                    break
                support.append(fact_doc[step_fact[st](cur, nxt)])
                cur = nxt
            else:
                pools.setdefault(len(steps), {}).setdefault(fmt, []).append(
                    {"question": fmt.format(e=e), "answer": cur, "hops": len(steps), "support": sorted(support)}
                )

    picked = rng.sample([x for fmt in sorted(pools[1]) for x in pools[1][fmt]], 60)
    for hops, quota in ((2, QUOTA_2HOP), (3, QUOTA_3HOP)):
        lists = [rng.sample(pools[hops][f], len(pools[hops][f])) for f in sorted(pools[hops])]
        got = []
        while len(got) < quota and any(lists):
            for lst in lists:
                if lst and len(got) < quota:
                    got.append(lst.pop())
        assert len(got) == quota, f"pool too small for {hops}-hop"
        picked += got
    rng.shuffle(picked)
    for n, q in enumerate(picked, 1):
        q["id"] = f"q{n:03d}"
    for hops in (1, 2, 3):
        grp = [q for q in picked if q["hops"] == hops]
        rng.shuffle(grp)
        for j, q in enumerate(grp):
            q["split"] = "dev" if j < len(grp) // 2 else "test"
    return docs, picked


def write(out, docs, questions):
    out = Path(out)
    (out / "corpus").mkdir(parents=True, exist_ok=True)
    for doc_id, text in docs.items():
        (out / "corpus" / f"{doc_id}.txt").write_text(text + "\n")
    lines = [json.dumps(q, sort_keys=True) for q in questions]
    (out / "questions.jsonl").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    args = ap.parse_args()
    d, q = build(SEED)
    write(args.out, d, q)
    print(f"wrote {len(d)} docs and {len(q)} questions to {args.out}")
