"""handoffpact: contract checks for the messages agents pass to each other."""

from .contract import (
    Contract,
    ContractError,
    FieldSpec,
    Result,
    Violation,
    check,
    load,
    load_dir,
    parse,
    semantic,
)
from .guard import HandoffBlocked, guard

__all__ = [
    "Contract",
    "ContractError",
    "FieldSpec",
    "HandoffBlocked",
    "Result",
    "Violation",
    "check",
    "guard",
    "load",
    "load_dir",
    "parse",
    "semantic",
]
__version__ = "0.1.0rc1"
