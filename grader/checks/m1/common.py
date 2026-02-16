# grader/checks/m1/common.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from grader.core.models import Message, Severity, CheckResult


def ok(check_id: str, title: str, possible: int, debug: Dict[str, Any] | None = None) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        title=title,
        earned=possible,
        possible=possible,
        passed=True,
        messages=[],
        debug=debug or {},
    )


def fail(
    check_id: str,
    title: str,
    earned: int,
    possible: int,
    messages: List[Message],
    debug: Dict[str, Any] | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        title=title,
        earned=max(0, min(earned, possible)),
        possible=possible,
        passed=False,
        messages=messages,
        debug=debug or {},
    )


def msg(sev: Severity, what: str, why: str, how: List[str], evidence: str = "") -> Message:
    return Message(severity=sev, what_failed=what, why=why, how_to_fix=how, evidence=evidence)
