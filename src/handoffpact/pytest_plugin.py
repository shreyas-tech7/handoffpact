"""pytest plugin: consumer-driven contract tests for agent handoffs.

A contract test replays recorded producer outputs into a consumer. It fails when
1. a recorded message breaks the contract (producer drift), or
2. the consumer reads a field the contract does not promise (consumer drift), or
3. the consumer raises on a message that keeps the contract.

Use the `handoff_pact` fixture:

    def test_draft_consumes_research(handoff_pact):
        handoff_pact.replay("contracts/research_to_draft.toml", "recordings/r2d.jsonl", draft)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .contract import Contract, check, load


class DriftError(AssertionError):
    """A recorded handoff and its consumer no longer agree with the contract."""


class TrackedDict(dict):
    """A dict that remembers every key that was read."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reads: set[str] = set()

    def __getitem__(self, key):
        self.reads.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.reads.add(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.reads.add(key)
        return super().__contains__(key)


def read_recordings(path: str | Path) -> list[dict]:
    """One JSON object per line: {"message": {...}, "context": {...}}."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


class HandoffPact:
    def replay(self, contract: Contract | str | Path, recordings, consumer) -> list[Any]:
        """Run `consumer(message)` on every recording. Return the consumer outputs."""
        if not isinstance(contract, Contract):
            contract = load(contract)
        if isinstance(recordings, str | Path):
            recordings = read_recordings(recordings)
        if not recordings:
            raise DriftError(f"{contract.name}: no recordings to replay")
        problems, outputs = [], []
        for i, rec in enumerate(recordings):
            res = check(contract, rec["message"], rec.get("context", {}))
            if not res.ok:
                lines = "; ".join(str(v) for v in res.violations)
                problems.append(f"recording {i}: producer drift: {lines}")
                continue
            msg = TrackedDict(rec["message"])
            try:
                outputs.append(consumer(msg))
            except Exception as exc:
                problems.append(f"recording {i}: consumer raised {type(exc).__name__}: {exc}")
                continue
            unpromised = sorted(msg.reads - set(contract.fields))
            if unpromised:
                problems.append(
                    f"recording {i}: consumer drift: reads {unpromised}, "
                    f"which contract {contract.name} does not promise"
                )
        if problems:
            raise DriftError("\n".join(problems))
        return outputs


@pytest.fixture
def handoff_pact() -> HandoffPact:
    return HandoffPact()
