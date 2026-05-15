from __future__ import annotations

from typing import Optional, List


class SemanticError(Exception):
    def __init__(self, message: str, lineno: Optional[int] = None) -> None:
        self.message: str = message
        self.lineno: Optional[int] = lineno
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.lineno is not None:
            return f"[Line {self.lineno}] Error: {self.message}"
        return f"Error: {self.message}"


class SemanticErrorCollector:
    def __init__(self) -> None:
        self.errors: List[SemanticError] = []

    def add_error(self, message: str, lineno: Optional[int] = None) -> None:
        self.errors.append(SemanticError(message, lineno))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> List[SemanticError]:
        return self.errors

    def report(self) -> str:
        if not self.errors:
            return "No errors found."
        lines: List[str] = [f"Found {len(self.errors)} error(s):"]
        for i, err in enumerate(self.errors, 1):
            lines.append(f"  {i}. {err}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.errors.clear()

