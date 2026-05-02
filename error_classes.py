class SemanticError(Exception):
    def __init__(self, message, lineno=None):
        self.message = message
        self.lineno = lineno
        super().__init__(self.__str__())

    def __str__(self):
        if self.lineno is not None:
            return f"[Line {self.lineno}] Error: {self.message}"
        return f"Error: {self.message}"


class SemanticErrorCollector:
    def __init__(self):
        self.errors: list[SemanticError] = []

    def add_error(self, message: str, lineno=None):
        self.errors.append(SemanticError(message, lineno))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> list[SemanticError]:
        return self.errors

    def report(self) -> str:
        if not self.errors:
            return "No errors found."
        lines = [f"Found {len(self.errors)} error(s):"]
        for i, err in enumerate(self.errors, 1):
            lines.append(f"  {i}. {err}")
        return "\n".join(lines)

    def clear(self):
        self.errors.clear()