"""Contracts for agent handoffs: load them from TOML and check a message against one.

A contract covers one edge in an agent graph (producer to consumer). It lists the
fields the producer promises, their types, enums, string length limits, ID references
that must exist in the producer's input context, and named semantic checks.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TYPES: dict[str, Callable[[Any], bool]] = {
    "str": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "dict": lambda v: isinstance(v, dict),
    "list": lambda v: isinstance(v, list),
}
FIELD_KEYS = {
    "type",
    "required",
    "enum",
    "min_length",
    "max_length",
    "min_items",
    "max_items",
    "ref",
}

_SEMANTIC: dict[str, Callable[[dict, dict], list[str] | str | None]] = {}


def semantic(name: str):
    """Register a semantic check by name. It gets (message, context) and returns None,
    True or an empty list when the message is fine, and False, a problem string or a
    list of problem strings when it is not."""

    def deco(fn):
        _SEMANTIC[name] = fn
        return fn

    return deco


def semantic_checks() -> dict[str, Callable]:
    return dict(_SEMANTIC)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    required: bool = True
    enum: tuple | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_items: int | None = None
    max_items: int | None = None
    ref: str | None = None

    @property
    def item_type(self) -> str | None:
        if self.type.startswith("list[") and self.type.endswith("]"):
            return self.type[5:-1]
        return None


@dataclass(frozen=True)
class Contract:
    name: str
    producer: str
    consumer: str
    fields: dict[str, FieldSpec]
    semantic: tuple[str, ...] = ()
    extra: str = "allow"
    description: str = ""
    source: str = ""


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.rule} ({self.detail})"


@dataclass
class Result:
    edge: str
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def __bool__(self) -> bool:
        return self.ok


class ContractError(ValueError):
    """The contract file itself is wrong."""


def _known_type(t: str) -> bool:
    inner = t[5:-1] if t.startswith("list[") and t.endswith("]") else None
    return t in TYPES or (inner is not None and inner in TYPES)


def _check_rules(source: str, fname: str, spec: dict) -> None:
    """Reject rules that cannot apply to the field's type, and rule values of the wrong type."""
    t = spec["type"]
    is_list = t == "list" or t.startswith("list[")
    inner = t[5:-1] if t.startswith("list[") else None
    stringy = t == "str" or inner == "str"
    for key in ("min_length", "max_length", "min_items", "max_items"):
        if key in spec and (not isinstance(spec[key], int) or isinstance(spec[key], bool)):
            raise ContractError(f"{source}: field {fname!r} rule {key} must be an integer")
    if ("min_length" in spec or "max_length" in spec) and not stringy:
        raise ContractError(f"{source}: field {fname!r} has a length rule but is not a string")
    if ("min_items" in spec or "max_items" in spec) and not is_list:
        raise ContractError(f"{source}: field {fname!r} has an items rule but is not a list")
    if "required" in spec and not isinstance(spec["required"], bool):
        raise ContractError(f"{source}: field {fname!r} rule required must be true or false")
    if "enum" in spec and not isinstance(spec["enum"], list):
        raise ContractError(f"{source}: field {fname!r} rule enum must be a list")
    if "ref" in spec and not isinstance(spec["ref"], str):
        raise ContractError(f"{source}: field {fname!r} rule ref must be a path string")


def parse(data: dict, source: str = "") -> Contract:
    edge = data.get("edge", {})
    for key in ("name", "producer", "consumer"):
        if not isinstance(edge.get(key), str) or not edge[key]:
            raise ContractError(f"{source}: [edge] needs a {key!r} string")
    fields = {}
    for fname, spec in data.get("fields", {}).items():
        unknown = set(spec) - FIELD_KEYS
        if unknown:
            raise ContractError(f"{source}: field {fname!r} has unknown keys {sorted(unknown)}")
        if not _known_type(spec.get("type", "")):
            raise ContractError(f"{source}: field {fname!r} has unknown type {spec.get('type')!r}")
        _check_rules(source, fname, spec)
        enum = tuple(spec["enum"]) if "enum" in spec else None
        fields[fname] = FieldSpec(name=fname, **{**spec, "enum": enum})
    if not fields:
        raise ContractError(f"{source}: a contract needs at least one field")
    checks = tuple(data.get("semantic", {}).get("checks", []))
    extra = edge.get("extra", "allow")
    if extra not in ("allow", "forbid"):
        raise ContractError(f"{source}: extra must be 'allow' or 'forbid'")
    return Contract(
        name=edge["name"],
        producer=edge["producer"],
        consumer=edge["consumer"],
        fields=fields,
        semantic=checks,
        extra=extra,
        description=edge.get("description", ""),
        source=source,
    )


def load(path: str | Path) -> Contract:
    path = Path(path)
    with path.open("rb") as f:
        return parse(tomllib.load(f), source=path.name)


def load_dir(directory: str | Path) -> dict[str, Contract]:
    out = {}
    for p in sorted(Path(directory).glob("*.toml")):
        c = load(p)
        out[c.name] = c
    return out


def resolve(context: Any, path: str) -> list[Any]:
    """Every value at a dotted path. `orders[*].order_id` walks each list item.
    A ref check also accepts any item of a list found at the path."""
    values = [context]
    for part in path.split("."):
        star = part.endswith("[*]")
        key = part[:-3] if star else part
        nxt = []
        for v in values:
            if isinstance(v, dict) and key in v:
                got = v[key]
                if star:
                    nxt.extend(got if isinstance(got, list) else [])
                else:
                    nxt.append(got)
        values = nxt
    return values


def _hashable(v: Any) -> bool:
    try:
        hash(v)
    except TypeError:
        return False
    return True


def _check_value(spec: FieldSpec, path: str, value: Any, refs: list | None) -> list[Violation]:
    t = spec.item_type or spec.type
    if not TYPES[t](value):
        return [Violation(path, "type", f"want {t}, got {type(value).__name__}")]
    out = []
    if spec.enum is not None and value not in spec.enum:
        out.append(Violation(path, "enum", f"{value!r} not in {list(spec.enum)}"))
    if isinstance(value, str):
        if spec.min_length is not None and len(value) < spec.min_length:
            out.append(Violation(path, "min_length", f"{len(value)} < {spec.min_length}"))
        if spec.max_length is not None and len(value) > spec.max_length:
            out.append(Violation(path, "max_length", f"{len(value)} > {spec.max_length}"))
    if refs is not None and (not _hashable(value) or value not in refs):
        out.append(Violation(path, "ref", f"{value!r} not found at context {spec.ref}"))
    return out


def _problems(got) -> list[str]:
    """None, True or an empty list mean pass. False, a string or a list of strings mean fail."""
    if got is None or got is True:
        return []
    if got is False:
        return ["check returned False"]
    if isinstance(got, str):
        return [got]
    if isinstance(got, list | tuple):
        return [str(p) for p in got]
    return [f"check returned {type(got).__name__}, want None, a bool, a string or a list"]


def check(edge: Contract, message: Any, context: dict | None = None) -> Result:
    """Check one handoff message. Returns a Result. `result.ok` is True when it passes."""
    context = context or {}
    res = Result(edge.name)
    v = res.violations
    if not isinstance(message, dict):
        v.append(Violation("$", "type", f"want dict, got {type(message).__name__}"))
        return res
    for name, spec in edge.fields.items():
        if name not in message:
            if spec.required:
                v.append(Violation(name, "required", "missing"))
            continue
        value = message[name]
        refs = None
        if spec.ref:
            found = resolve(context, spec.ref)
            flat = [x for r in found for x in (r if isinstance(r, list) else [r])]
            refs = [r for r in flat if _hashable(r)]
        if spec.item_type or spec.type == "list":
            if not isinstance(value, list):
                v.append(Violation(name, "type", f"want {spec.type}, got {type(value).__name__}"))
                continue
            if spec.min_items is not None and len(value) < spec.min_items:
                v.append(Violation(name, "min_items", f"{len(value)} < {spec.min_items}"))
            if spec.max_items is not None and len(value) > spec.max_items:
                v.append(Violation(name, "max_items", f"{len(value)} > {spec.max_items}"))
            if spec.item_type:
                for i, item in enumerate(value):
                    v.extend(_check_value(spec, f"{name}[{i}]", item, refs))
        else:
            v.extend(_check_value(spec, name, value, refs))
    if edge.extra == "forbid":
        for name in message:
            if name not in edge.fields:
                v.append(Violation(name, "extra", "field not in contract"))
    for cname in edge.semantic:
        fn = _SEMANTIC.get(cname)
        if fn is None:
            v.append(Violation("$", f"semantic:{cname}", "check is not registered"))
            continue
        try:
            problems = _problems(fn(message, context))
        except Exception as exc:  # a crashing check is a failed check, not a crash
            problems = [f"check raised {type(exc).__name__}: {exc}"]
        for p in problems:
            v.append(Violation("$", f"semantic:{cname}", p))
    return res
