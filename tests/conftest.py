from pathlib import Path

import pytest

from common import load_corpus, load_questions

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def docs():
    return load_corpus(ROOT / "corpus")


@pytest.fixture(scope="session")
def questions():
    return load_questions(ROOT / "questions.jsonl")
