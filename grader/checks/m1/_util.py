# grader/checks/m1/_util.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from grader.core.context import GradingContext


def repo(ctx: GradingContext) -> Path:
    return ctx.repo_path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def evidence_path(rel: str, exists: bool | None = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {"path": rel}
    if exists is not None:
        d["exists"] = bool(exists)
    return d


def item(
    *,
    item_id: str,
    title: str,
    severity: str,
    score: int,
    max_score: int,
    what_failed: str = "",
    how_to_fix: Optional[List[str]] = None,
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    passed = (int(score) == int(max_score))
    return {
        "id": item_id,
        "title": title,
        "severity": severity,
        "score": int(score),
        "max_score": int(max_score),
        "passed": passed,
        "what_failed": "" if passed else (what_failed or ""),
        "how_to_fix": "" if passed else ("\n".join(how_to_fix or [])),
        "evidence": evidence or {},
        "comment": "",
    }