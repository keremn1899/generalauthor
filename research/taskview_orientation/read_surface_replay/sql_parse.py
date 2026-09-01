"""Restricted, mechanical SQL classification for the sealed TaskView workload.

The parser does not infer intent.  Anything outside the observed one-relation
``SELECT *`` subset is retained as an escape-hatch query.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_KEYWORD = {
    "SELECT",
    "FROM",
    "WHERE",
    "AND",
    "OR",
    "ORDER",
    "BY",
    "ASC",
    "DESC",
    "LIMIT",
    "LIKE",
    "NOT",
    "NULL",
    "IS",
    "WITH",
    "JOIN",
    "UNION",
    "INTERSECT",
    "EXCEPT",
    "GROUP",
    "HAVING",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
}


@dataclass(frozen=True)
class FilterPred:
    column: str
    op: str
    value: str | int | float | None


@dataclass(frozen=True)
class RestrictedQuery:
    raw_sql: str
    relation: str | None
    projection: str
    filters: tuple[FilterPred, ...]
    connector: str
    order: tuple[tuple[str, str], ...]
    limit: int | None
    select_star: bool
    single_relation: bool
    has_join: bool
    has_subquery: bool
    has_cte: bool
    has_aggregate: bool
    has_set_operation: bool
    parsed: bool
    shape: str
    simple_kind: str
    sql_escape_required: bool

    def query_key(self) -> str:
        if not self.parsed:
            return f"escape:{self.raw_sql.strip()}"
        filters = ",".join(
            f"{item.column}{item.op}{item.value!r}" for item in self.filters
        )
        order = ",".join(f"{column}:{direction}" for column, direction in self.order)
        return (
            f"{self.relation}|*|f={self.connector}:{filters}|o={order}|l={self.limit}"
        )


def _tokens(sql: str) -> list[tuple[str, str]]:
    text = sql.strip().rstrip(";").strip()
    out: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "'" :
            index += 1
            buf = []
            while index < len(text):
                if text[index] == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    buf.append("'")
                    index += 2
                    continue
                if text[index] == "'":
                    index += 1
                    break
                buf.append(text[index])
                index += 1
            else:
                raise ValueError("unterminated string")
            out.append(("STRING", "".join(buf)))
            continue
        if char == "*":
            out.append(("STAR", "*"))
            index += 1
            continue
        if char in "=<>":
            out.append(("OP", char))
            index += 1
            continue
        if char.isdigit():
            start = index
            while index < len(text) and (text[index].isdigit() or text[index] == "."):
                index += 1
            out.append(("NUMBER", text[start:index]))
            continue
        match = _IDENT.match(text, index)
        if match:
            word = match.group(0)
            upper = word.upper()
            kind = "KEYWORD" if upper in _KEYWORD else "IDENT"
            out.append((kind, upper if kind == "KEYWORD" else word))
            index = match.end()
            continue
        raise ValueError(f"unexpected character {char!r}")
    return out


def _flags(sql: str) -> dict[str, bool]:
    return {
        "has_join": bool(re.search(r"(?i)\bJOIN\b", sql)),
        "has_subquery": bool(re.search(r"(?i)\(\s*SELECT\b", sql)),
        "has_cte": bool(re.search(r"(?is)^\s*WITH\b", sql)),
        "has_aggregate": bool(
            re.search(r"(?i)\b(COUNT|SUM|AVG|MIN|MAX|GROUP\s+BY|HAVING)\b", sql)
        ),
        "has_set_operation": bool(
            re.search(r"(?i)\b(UNION|INTERSECT|EXCEPT)\b", sql)
        ),
        "select_star": bool(re.search(r"(?is)^\s*SELECT\s+\*", sql.strip().rstrip(";"))),
        "single_relation": len(re.findall(r"(?i)\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)", sql))
        == 1,
    }


def _parse_value(tokens: list[tuple[str, str]], index: int) -> tuple[Any, int]:
    kind, value = tokens[index]
    if kind == "STRING":
        return value, index + 1
    if kind == "NUMBER":
        if "." in value:
            return float(value), index + 1
        return int(value), index + 1
    raise ValueError("expected literal")


def _parse_pred(tokens: list[tuple[str, str]], index: int) -> tuple[FilterPred, int]:
    if tokens[index][0] != "IDENT":
        raise ValueError("expected column")
    column = tokens[index][1]
    index += 1
    if index >= len(tokens):
        raise ValueError("expected predicate operator")
    kind, value = tokens[index]
    if kind == "OP" and value == "=":
        literal, index = _parse_value(tokens, index + 1)
        return FilterPred(column, "=", literal), index
    if kind == "KEYWORD" and value == "LIKE":
        literal, index = _parse_value(tokens, index + 1)
        if not isinstance(literal, str):
            raise ValueError("LIKE requires a string")
        return FilterPred(column, "LIKE", literal), index
    raise ValueError("unsupported predicate")


def parse_sql(sql: str) -> RestrictedQuery:
    raw = str(sql or "")
    flags = _flags(raw)
    try:
        tokens = _tokens(raw)
        index = 0

        def expect(*allowed: tuple[str, str | None]) -> tuple[str, str]:
            nonlocal index
            if index >= len(tokens):
                raise ValueError("unexpected end of SQL")
            kind, value = tokens[index]
            for allowed_kind, allowed_value in allowed:
                if kind == allowed_kind and (
                    allowed_value is None or value == allowed_value
                ):
                    index += 1
                    return kind, value
            raise ValueError(f"unexpected token {kind}:{value}")

        expect(("KEYWORD", "SELECT"))
        expect(("STAR", None))
        expect(("KEYWORD", "FROM"))
        _, relation = expect(("IDENT", None))
        filters: list[FilterPred] = []
        connector = ""
        order: list[tuple[str, str]] = []
        limit: int | None = None
        if index < len(tokens) and tokens[index] == ("KEYWORD", "WHERE"):
            index += 1
            pred, index = _parse_pred(tokens, index)
            filters.append(pred)
            if index < len(tokens) and tokens[index][0] == "KEYWORD" and tokens[index][1] in {
                "AND",
                "OR",
            }:
                connector = tokens[index][1]
                index += 1
                while True:
                    pred, index = _parse_pred(tokens, index)
                    filters.append(pred)
                    if (
                        index < len(tokens)
                        and tokens[index][0] == "KEYWORD"
                        and tokens[index][1] == connector
                    ):
                        index += 1
                        continue
                    break
        if index < len(tokens) and tokens[index] == ("KEYWORD", "ORDER"):
            index += 1
            expect(("KEYWORD", "BY"))
            while True:
                _, column = expect(("IDENT", None))
                direction = "ASC"
                if index < len(tokens) and tokens[index][0] == "KEYWORD" and tokens[index][1] in {
                    "ASC",
                    "DESC",
                }:
                    direction = tokens[index][1]
                    index += 1
                order.append((column, direction))
                if index < len(tokens) and tokens[index] == ("IDENT", None):
                    # comma-less extra ident is invalid; restricted grammar has no comma token
                    raise ValueError("ORDER BY columns must be comma-separated")
                break
        if index < len(tokens) and tokens[index] == ("KEYWORD", "LIMIT"):
            index += 1
            _, number = expect(("NUMBER", None))
            limit = int(number)
        if index != len(tokens):
            raise ValueError("trailing SQL")
        parsed = True
    except (ValueError, IndexError):
        parsed = False
        relation = None
        filters = []
        connector = ""
        order = []
        limit = None

    if not parsed:
        shape = "ESCAPE"
        simple_kind = "escape"
        sql_escape = True
    elif filters and (order or limit is not None):
        shape = "FILTER+ORDER/LIMIT"
        simple_kind = "select"
        sql_escape = False
    elif filters:
        if (
            len(filters) == 1
            and filters[0].op == "="
            and connector == ""
            and not order
            and limit is None
        ):
            shape = "FILTER"
            simple_kind = "equality_get"
        else:
            shape = "FILTER"
            simple_kind = "select"
        sql_escape = False
    elif order or limit is not None:
        shape = "ORDER/LIMIT"
        simple_kind = "select"
        sql_escape = False
    else:
        shape = "PLAIN"
        simple_kind = "enumeration"
        sql_escape = False

    return RestrictedQuery(
        raw_sql=raw,
        relation=relation if parsed else None,
        projection="*" if flags["select_star"] else "other",
        filters=tuple(filters),
        connector=connector,
        order=tuple(order),
        limit=limit,
        select_star=flags["select_star"],
        single_relation=flags["single_relation"],
        has_join=flags["has_join"],
        has_subquery=flags["has_subquery"],
        has_cte=flags["has_cte"],
        has_aggregate=flags["has_aggregate"],
        has_set_operation=flags["has_set_operation"],
        parsed=parsed,
        shape=shape,
        simple_kind=simple_kind,
        sql_escape_required=sql_escape or not flags["single_relation"] or not flags["select_star"],
    )


def classify_sql_corpus(statements: list[str]) -> dict[str, int]:
    parsed = [parse_sql(sql) for sql in statements]
    return {
        "query_sql_calls": len(parsed),
        "plain_enumerations": sum(item.shape == "PLAIN" for item in parsed),
        "filtered_calls": sum(item.shape == "FILTER" for item in parsed),
        "order_limit_variants": sum(item.shape == "ORDER/LIMIT" for item in parsed),
        "single_relation": sum(item.single_relation for item in parsed),
        "select_star": sum(item.select_star for item in parsed),
        "join": sum(item.has_join for item in parsed),
        "subquery": sum(item.has_subquery for item in parsed),
        "cte": sum(item.has_cte for item in parsed),
        "aggregate": sum(item.has_aggregate for item in parsed),
        "set_operation": sum(item.has_set_operation for item in parsed),
        "unparsed": sum(not item.parsed for item in parsed),
    }
