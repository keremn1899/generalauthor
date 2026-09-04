"""AST ablation of one named semantic element. No model repair."""

from __future__ import annotations

import ast
from typing import Any


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _first_str(node: ast.Call) -> str | None:
    if not node.args:
        return None
    arg0 = node.args[0]
    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
        return arg0.value
    if isinstance(arg0, ast.JoinedStr):
        parts: list[str] = []
        for value in arg0.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
                parts.append("{" + value.value.id + "}")
        return "".join(parts)
    return None


class StripElement(ast.NodeTransformer):
    def __init__(
        self,
        *,
        requirement_names: set[str] | None = None,
        unresolved_names: set[str] | None = None,
        drop_seasonal_loop: bool = False,
    ) -> None:
        self.requirement_names = requirement_names or set()
        self.unresolved_names = unresolved_names or set()
        self.drop_seasonal_loop = drop_seasonal_loop
        self.removed = 0

    def _match(self, node: ast.Call) -> bool:
        name = _call_name(node)
        arg = _first_str(node)
        if name in {"require", "require_unique", "require_materializable", "require_interpreted", "require_numeric"}:
            if arg in self.requirement_names:
                return True
            if arg and arg.startswith("seasonal_{") and "interpret_seasonal_month" in self.requirement_names:
                return True
        if name == "unresolved" and arg in self.unresolved_names:
            return True
        return False

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if isinstance(node.value, ast.Call) and self._match(node.value):
            self.removed += 1
            return None
        return self.generic_visit(node)

    def visit_For(self, node: ast.For) -> ast.AST | None:
        if self.drop_seasonal_loop:
            target = node.target
            if isinstance(target, ast.Name) and target.id == "month":
                self.removed += 1
                return None
        node = self.generic_visit(node)
        if not getattr(node, "body", None):
            return None
        return node

    def visit_If(self, node: ast.If) -> ast.AST | None:
        node = self.generic_visit(node)
        if not node.body:
            if node.orelse:
                node.body = [ast.Pass()]
            else:
                return None
        return node


def ablate_source(
    code: str,
    *,
    requirement_names: list[str] | None = None,
    unresolved_names: list[str] | None = None,
    drop_seasonal_loop: bool = False,
) -> tuple[str, int]:
    tree = ast.parse(code)
    stripper = StripElement(
        requirement_names=set(requirement_names or []),
        unresolved_names=set(unresolved_names or []),
        drop_seasonal_loop=drop_seasonal_loop,
    )
    new_tree = stripper.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree) + "\n", stripper.removed
