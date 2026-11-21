"""The decorator: check an agent's input and output at the boundary."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable

from .contract import Contract, Result, check

log = logging.getLogger("handoffpact")


class HandoffBlocked(RuntimeError):
    """A handoff broke its contract in stop mode. The next agent never sees it."""

    def __init__(self, result: Result):
        self.result = result
        lines = "; ".join(str(v) for v in result.violations)
        super().__init__(f"handoff {result.edge} blocked: {lines}")


def guard(
    outbound: Contract | None = None,
    inbound: Contract | None = None,
    mode: str = "stop",
    inbound_context: Callable[[dict], dict] | None = None,
    on_violation: Callable[[Result], None] | None = None,
):
    """Wrap an agent function `fn(inp) -> out`.

    The output is checked against `outbound`. The agent's own input is the context,
    because ID references must exist in the producer's input context. If `inbound`
    is given, the input is checked too, with `inbound_context(inp)` as context.
    In "stop" mode a violation raises HandoffBlocked. In "warn" mode it is logged and
    passed to `on_violation`, and the message goes through.
    """
    if mode not in ("stop", "warn"):
        raise ValueError("mode must be 'stop' or 'warn'")

    def handle(result: Result) -> None:
        if result.ok:
            return
        if on_violation:
            on_violation(result)
        if mode == "stop":
            raise HandoffBlocked(result)
        log.warning("handoff %s broke its contract: %s", result.edge, result.violations)

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(inp, *args, **kwargs):
            if inbound is not None:
                ctx = inbound_context(inp) if inbound_context else {}
                handle(check(inbound, inp, ctx))
            out = fn(inp, *args, **kwargs)
            if outbound is not None:
                handle(check(outbound, out, inp))
            return out

        return wrapper

    return deco
