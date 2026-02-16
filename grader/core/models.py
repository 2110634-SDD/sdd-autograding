# grader/core/models.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    SUGGESTION = "SUGGESTION"


@dataclass
class Message:
    severity: Severity
    what_failed: str
    why: str
    how_to_fix: List[str]
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class CheckResult:
    check_id: str
    title: str
    earned: int
    possible: int
    passed: bool
    messages: List[Message]
    debug: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "title": self.title,
            "earned": self.earned,
            "possible": self.possible,
            "passed": self.passed,
            "messages": [m.to_dict() for m in self.messages],
            "debug": self.debug or {},
        }


@dataclass
class CategoryResult:
    category_id: str
    title: str
    checks: List[CheckResult]

    @property
    def earned(self) -> int:
        return sum(c.earned for c in self.checks)

    @property
    def possible(self) -> int:
        return sum(c.possible for c in self.checks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "title": self.title,
            "earned": self.earned,
            "possible": self.possible,
            "checks": [c.to_dict() for c in self.checks],
        }
