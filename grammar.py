"""Fact sentences and question templates of the synthetic corpus."""
import re

NAME = r"[A-Z][a-z]+(?: [A-Z][a-z]+)?"

FACT_FORMATS = {
    "owns": "The {a} team owns the {b} system.",
    "leads": "{a} leads the {b} team.",
    "reports_to": "{a} reports to {b}.",
    "depends_on": "The {a} system depends on the {b} system.",
}

# step -> (relation, direction). "out": current entity is the subject; "in": the object.
STEPS = {
    "owner": ("owns", "in"),
    "lead": ("leads", "in"),
    "led": ("leads", "out"),
    "boss": ("reports_to", "out"),
    "dep": ("depends_on", "out"),
}
START_KIND = {"owner": "system", "lead": "team", "led": "person", "boss": "person", "dep": "system"}

TEMPLATES = (
    ("Which team owns the {e} system?", ("owner",)),
    ("Who leads the {e} team?", ("lead",)),
    ("Which team does {e} lead?", ("led",)),
    ("Who does {e} report to?", ("boss",)),
    ("Which system does the {e} system depend on?", ("dep",)),
    ("Who leads the team that owns the {e} system?", ("owner", "lead")),
    ("Who does the lead of the {e} team report to?", ("lead", "boss")),
    ("Which team owns the system that the {e} system depends on?", ("dep", "owner")),
    ("Who does the person that {e} reports to report to?", ("boss", "boss")),
    ("Which system does the system that the {e} system depends on depend on?", ("dep", "dep")),
    ("Who does the lead of the team that owns the {e} system report to?", ("owner", "lead", "boss")),
    ("Who leads the team that owns the system that the {e} system depends on?", ("dep", "owner", "lead")),
    ("Which team owns the system that the system that the {e} system depends on depends on?", ("dep", "dep", "owner")),
)


def _compile(fmt):
    parts = re.split(r"(\{\w+\})", fmt)
    return re.compile("".join(f"(?P<{p[1:-1]}>{NAME})" if p.startswith("{") else re.escape(p) for p in parts))


FACT_RX = {rel: _compile(fmt) for rel, fmt in FACT_FORMATS.items()}
QUESTION_RX = [(_compile(fmt), steps) for fmt, steps in TEMPLATES]


def parse_question(question):
    for rx, steps in QUESTION_RX:
        m = rx.fullmatch(question)
        if m:
            return steps, m["e"]
    return None


def normalize(question):
    return " ".join(question.lower().split()).rstrip("?").strip()
