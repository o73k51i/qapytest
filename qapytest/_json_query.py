"""Module providing lightweight query utilities for navigating and extracting data from JSON-like Python objects."""

from __future__ import annotations

import contextlib
import re
from typing import Any, TypeAlias

JsonValue: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None

_TOKEN_RE = re.compile(
    r"\.\.([^.\[\]]+)"
    r"|\[(-?\d+)\]"
    r"|\[\?([^!=\]]+)(!=|=)([^\]]+)\]"
    r"|\[\?([^\]]+)\]"
    r"|\[\]"
    r"|\.([^.\[\]]+)",
)

_PIPE_FN_RE = re.compile(r"(sort_desc|sort|min|max)\(([^)]+)\)")
_PIPE_OP_RE = re.compile(
    r"^(unique|count|first|last|sort_desc\([^)]+\)|sort\([^)]+\)|min\([^)]+\)|max\([^)]+\))(.*)",
)


def find_values(obj: JsonValue, path: str) -> list:
    """Return all matches for *path* in *obj* as a list.

    Always returns a list — empty when nothing matches.

    Supports the following path syntax:

    - ``.key`` — navigate into a dict key.
    - ``[]`` — fan out over every element of a list.
    - ``[N]`` / ``[-N]`` — pick a single element by index.
    - ``[?key=value]`` / ``[?key!=value]`` — filter by equality or inequality.
      Supports JSON literals: ``null``, ``true``, ``false``.
    - ``[?key]`` — keep only elements where *key* is truthy.
    - ``..key`` — recursive descent, collecting *key* at any depth.

    Pipe operators can be appended with ``|`` to transform results:
    ``unique``, ``count``, ``first``, ``last``,
    ``sort(key)``, ``sort_desc(key)``, ``min(key)``, ``max(key)``.

    Args:
        obj: Any JSON-like Python object (dict, list, or scalar).
        path: Query path using the syntax described above.

    Returns:
        list: All matched values, or an empty list when nothing matches.

    ---
    ### Example usage:

    ```python
    data = {"users": [{"id": 1, "role": "admin"}, {"id": 2, "role": "user"}]}

    find_values(data, ".users[].id")              # [1, 2]
    find_values(data, ".users[?role=admin].id")   # [1]
    find_values(data, "..role")                   # ['admin', 'user']
    find_values(data, ".missing")                 # []
    find_values(data, ".users[]|sort_desc(id)")   # [{'id': 2, ...}, {'id': 1, ...}]
    find_values(data, ".users[]|count")           # [2]
    find_values(data, "..role|unique")            # ['admin', 'user']
    ```
    """
    path_part, *pipe_parts = _split_pipes(path)
    nodes = _eval([obj], _tokenize(path_part))
    for pipe in pipe_parts:
        pipe_op = pipe.strip()
        m = _PIPE_OP_RE.match(pipe_op)
        if m:
            nodes = _apply_pipe(nodes, m.group(1))
            if m.group(2):
                nodes = _eval(nodes, _tokenize(m.group(2)))
        else:
            nodes = _apply_pipe(nodes, pipe_op)
    return nodes


def find_value(obj: JsonValue, path: str) -> JsonValue:
    """Return the first match for *path* in *obj*, or ``None`` if not found.

    Args:
        obj: Any JSON-like Python object (dict, list, or scalar).
        path: Query path — see :func:`find_values` for the full syntax reference.

    Returns:
        JsonValue: The first matched value, or ``None`` when nothing matches.

    ---
    ### Example usage:

    ```python
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

    find_value(data, ".users[0].name")  # 'Alice'
    find_value(data, ".missing")        # None
    ```
    """
    result = find_values(obj, path)
    return result[0] if result else None


_JSON_LITERALS = {"null": None, "true": True, "false": False}


def _parse_literal(value: str) -> JsonValue:
    """Convert a filter value string to a Python object, mapping JSON literals."""
    if value in _JSON_LITERALS:
        return _JSON_LITERALS[value]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _split_pipes(path: str) -> list[str]:
    """Split a path string at ``|`` boundaries that are not inside brackets."""
    parts, current, depth = [], [], 0
    for ch in path:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "|" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def _apply_pipe(nodes: list, pipe: str) -> list:
    """Apply a single pipe operator to the current node list and return the result."""
    if pipe == "unique":
        seen: list = []
        for n in nodes:
            if n not in seen:
                seen.append(n)
        return seen

    if pipe == "count":
        return [len(nodes)]

    if pipe == "first":
        return [nodes[0]] if nodes else []

    if pipe == "last":
        return [nodes[-1]] if nodes else []

    m = _PIPE_FN_RE.fullmatch(pipe)
    if m:
        fn, key = m.group(1), m.group(2)

        def _key_fn(item: JsonValue) -> Any:  # noqa: ANN401
            key_path = key if key.startswith(".") else f".{key}"
            v = find_values(item, key_path)
            return v[0] if v else None

        if fn in ("sort", "sort_desc"):
            try:
                return sorted(nodes, key=_key_fn, reverse=(fn == "sort_desc"))
            except TypeError:
                return nodes

        if fn == "min":
            try:
                return [min(nodes, key=_key_fn)]
            except (ValueError, TypeError):
                return []

        if fn == "max":
            try:
                return [max(nodes, key=_key_fn)]
            except (ValueError, TypeError):
                return []

    return nodes


def _tokenize(path: str) -> list[tuple[str, str | int | None, JsonValue]]:
    tokens = []
    for m in _TOKEN_RE.finditer(path.strip()):
        (
            recurse_key,
            idx,
            filter_key,
            filter_op,
            filter_val,
            exist_key,
            nav_key,
        ) = m.groups()
        if recurse_key is not None:
            tokens.append(("recurse", recurse_key, None))
        elif idx is not None:
            tokens.append(("index", int(idx), None))
        elif filter_key is not None:
            op_token = "filter_ne" if filter_op == "!=" else "filter"
            normalized = filter_key if filter_key.startswith(".") else f".{filter_key}"
            tokens.append((op_token, normalized, _parse_literal(filter_val)))
        elif exist_key is not None:
            normalized = exist_key if exist_key.startswith(".") else f".{exist_key}"
            tokens.append(("exist", normalized, None))
        elif m.group(0) == "[]":
            tokens.append(("iter", None, None))
        elif nav_key is not None:
            tokens.append(("key", nav_key, None))
    return tokens


def _eval(nodes: list, tokens: list) -> list:
    if not tokens:
        return nodes

    (op, arg, arg2), *rest = tokens

    if op == "key":
        return _eval(
            [node[arg] for node in nodes if isinstance(node, dict) and arg in node],
            rest,
        )

    if op == "iter":
        return _eval(
            [item for node in nodes if isinstance(node, list) for item in node],
            rest,
        )

    if op == "index":
        next_nodes = []
        for node in nodes:
            if isinstance(node, list):
                with contextlib.suppress(IndexError):
                    next_nodes.append(node[arg])
        return _eval(next_nodes, rest)

    if op in ("filter", "filter_ne"):
        next_nodes = []
        for node in nodes:
            if isinstance(node, list):
                for item in node:
                    values = find_values(item, arg)
                    key_found = bool(values)
                    hit = key_found and values[0] == arg2
                    if (op == "filter" and hit) or (op == "filter_ne" and key_found and not hit):
                        next_nodes.append(item)
        return _eval(next_nodes, rest)

    if op == "exist":
        next_nodes = []
        for node in nodes:
            if isinstance(node, list):
                for item in node:
                    values = find_values(item, arg)
                    if values and values[0]:
                        next_nodes.append(item)
        return _eval(next_nodes, rest)

    if op == "recurse":
        return _eval(_collect_all(nodes, arg), rest)

    return nodes


def _collect_all(nodes: list, key: str) -> list:
    results = []
    for node in nodes:
        if isinstance(node, dict):
            if key in node:
                results.append(node[key])
            results.extend(_collect_all(list(node.values()), key))
        elif isinstance(node, list):
            results.extend(_collect_all(node, key))
    return results
