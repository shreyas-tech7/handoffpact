"""Docs generator: contract pages and a mermaid graph."""

from handoffpact import parse
from handoffpact.docsgen import generate, mermaid, page
from handoffpact.sample.pipeline import CONTRACTS_DIR, EDGES


def test_generates_a_page_per_contract_and_the_graph(tmp_path):
    files = generate(CONTRACTS_DIR, tmp_path, order=EDGES)
    names = sorted(p.name for p in files)
    assert names == sorted([f"{e}.md" for e in EDGES] + ["README.md"])
    index = (tmp_path / "README.md").read_text()
    assert "```mermaid" in index and "flowchart LR" in index
    assert index.count("-->|") == 4
    assert 'n_intake -->|"intake_to_research"| n_research' in index
    r2d = (tmp_path / "research_to_draft.md").read_text()
    assert "`order_total_matches`" not in r2d and "`order_facts_match`" in r2d
    assert "must exist at context `corpus[*].id`" in r2d


def test_mermaid_escapes_awkward_names():
    """Broken case: a quote, pipe or bracket in a name would break the mermaid syntax."""
    c = parse(
        {
            "edge": {"name": 'bad "edge" | [x]', "producer": "agent one", "consumer": "agent-2"},
            "fields": {"f": {"type": "str"}},
        }
    )
    m = mermaid([c])
    edge_line = m.splitlines()[-1]
    assert edge_line.count("|") == 2 and edge_line.count('"') == 2
    assert "n_agent_one" in m and "n_agent_2" in m
    assert "#quot;edge#quot; #124; #91;x#93;" in m


def test_page_lists_rules():
    c = parse(
        {
            "edge": {"name": "e", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "enum": ["x|y"], "required": False}},
        }
    )
    text = page(c)
    assert "| `f` | `str` | no |" in text and "x\\|y" in text
