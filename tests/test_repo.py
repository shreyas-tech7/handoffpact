"""Repo quality bar: README parts in order, generated numbers in sync, writing rules, files."""

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from handoffpact.report import FINAL, write

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"```.*?```", re.S)
CODE = re.compile(r"`[^`]*`")
GEN = re.compile(r"<!-- gen:(\w+) -->.*?<!-- /gen:\1 -->", re.S)
SECTIONS = [
    "## The problem",
    "## How it works",
    "## Results",
    "## Cost per task",
    "## Run it in 10 minutes",
    "## Limits",
    "## Glossary",
    "## Related work",
    "## How this was built",
]


def test_readme_parts_in_order():
    text = (ROOT / "README.md").read_text()
    status = text.index("**Status:**")
    pos = [text.index(s) for s in SECTIONS]
    assert status < pos[0] and pos == sorted(pos)
    assert "```mermaid" in text and "badge.svg" in text
    assert "injected by script" in text and "Faults from real models can look different" in text
    assert "docs/build/BUILD_PROMPT.md" in text and "not done yet" in text


def test_readme_numbers_match_results_files():
    """Broken case: someone types a number into the README by hand."""
    assert write(ROOT, check=True) == []
    res = json.loads((ROOT / FINAL).read_text())
    o = res["overall"]["detected"]
    text = (ROOT / "README.md").read_text()
    assert f"{o['k']}/{o['n']} = {100 * o['rate']:.1f}%" in text


def test_no_percent_outside_generated_blocks():
    """Broken case: a result typed into the prose. Only the glossary may say 95%."""
    text = GEN.sub("", FENCE.sub("", (ROOT / "README.md").read_text()))
    found = re.findall(r"\d+(?:\.\d+)?%", text)
    assert found == ["95%"], found


def test_results_meet_the_brief():
    res = json.loads((ROOT / FINAL).read_text())
    assert res["meta"]["fault_runs"] >= 500 and res["meta"]["clean_runs"] >= 200
    assert set(res["by_type"]) == {
        "drop",
        "wrong_type",
        "invented_id",
        "truncate",
        "stale",
        "leak",
        "swap",
    }
    for t in res["by_type"].values():
        assert t["detected"]["lo"] <= t["detected"]["rate"] <= t["detected"]["hi"]
    assert "blast_on" in res["overall"] and "blast_off" in res["overall"]


def _prose(path: Path) -> str:
    return CODE.sub("", FENCE.sub("", path.read_text(encoding="utf-8")))


DOCS = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"] + [
    p for p in sorted((ROOT / "docs").glob("*.md")) if p.name not in {"DEMO.md"}
]


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_writing_rules(path):
    text = _prose(path)
    assert "—" not in text and "–" not in text, "no em or en dashes"
    assert " - " not in re.sub(r"\n\s*- ", "\n", text), "no dashes as punctuation"
    for line in text.splitlines():
        if not line.startswith("|"):
            assert ";" not in line, f"semicolon in prose: {line}"
    for bad in ("it is important to note", "testament", "pivotal", "seamless", "delve"):
        assert bad not in text.lower()


def test_ship_files():
    for f in [
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        ".env.example",
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        "docs/index.html",
        "docs/DEMO.md",
        "docs/topics.txt",
        "docs/GITHUB_ABOUT.md",
        "docs/WALKTHROUGH.md",
        "docs/INTERVIEW_QA.md",
        "docs/HUMAN_STEPS.md",
        "docs/build/BUILD_PROMPT.md",
        "docs/contracts/README.md",
    ]:
        assert (ROOT / f).is_file(), f
    assert "Copyright (c) 2026 Shreyas" in (ROOT / "LICENSE").read_text()


def test_social_preview_size():
    head = (ROOT / "docs" / "social-preview.png").read_bytes()[:24]
    assert struct.unpack(">II", head[16:24]) == (1280, 640)


def test_topics():
    topics = (ROOT / "docs" / "topics.txt").read_text().split()
    assert 5 <= len(topics) <= 20
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,24}", t) for t in topics)


def test_generated_contract_docs_are_current(tmp_path):
    from handoffpact.docsgen import generate
    from handoffpact.sample.pipeline import CONTRACTS_DIR, EDGES

    for p in generate(CONTRACTS_DIR, tmp_path, order=EDGES):
        assert p.read_text() == (ROOT / "docs" / "contracts" / p.name).read_text(), p.name


def test_link_check_passes():
    r = subprocess.run(  # noqa: S603 (fixed argv, our own script)
        [sys.executable, str(ROOT / "scripts" / "check_links.py")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stdout
