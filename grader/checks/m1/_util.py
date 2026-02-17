# grader/checks/m1/_util.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from grader.core.context import GradingContext


# -----------------------------
# Repo / file helpers
# -----------------------------
def repo(ctx: GradingContext) -> Path:
    """
    Return root path of the student repository.
    Checks should use this as the base to locate required files.
    """
    return Path(ctx.repo_path)


def read_text(path: Path, *, default: str = "", encoding: str = "utf-8") -> str:
    """
    Safe file reader. Never raises; returns default if missing/unreadable.
    """
    try:
        return path.read_text(encoding=encoding)
    except Exception:
        return default


# -----------------------------
# Evidence helpers
# -----------------------------
def evidence_path(path: str, exists: bool) -> Dict[str, Any]:
    """
    Standard evidence about a file path existence.
    """
    return {"path": path, "text": f"{path} exists={exists}"}


def evidence_text(path: str, text: str, *, line: Optional[int] = None, col: Optional[int] = None) -> Dict[str, Any]:
    """
    Evidence with file path + optional location.
    """
    ev: Dict[str, Any] = {"path": path, "text": text}
    if isinstance(line, int):
        ev["line"] = line
    if isinstance(col, int):
        ev["col"] = col
    return ev


# -----------------------------
# Standard item builder
# -----------------------------
def item(
    *args: Any,
    id: Optional[str] = None,
    title: Optional[str] = None,
    severity: str = "INFO",
    score: int = 0,
    max_score: int = 0,
    passed: Optional[bool] = None,
    what_failed: str = "",
    how_to_fix: str = "",
    evidence: Any = None,
) -> Dict[str, Any]:
    """
    Build a standardized check-item dict.

    Supports BOTH calling styles:

    1) New keyword style (recommended):
       item(
         id="M1.X.01", title="...", severity="BLOCKER",
         score=0, max_score=1,
         what_failed="...", how_to_fix="...", evidence=...
       )

    2) Legacy positional style (kept for compatibility):
       item("M1.X.01", "Title", "BLOCKER", 0, 1, evidence=...)

       Positional mapping:
         args[0] -> id
         args[1] -> title
         args[2] -> severity
         args[3] -> score
         args[4] -> max_score
    """
    if args:
        if len(args) > 5:
            raise TypeError(f"item() accepts at most 5 positional args, got {len(args)}")

        if id is None and len(args) >= 1:
            id = args[0]
        if title is None and len(args) >= 2:
            title = args[1]
        if len(args) >= 3:
            severity = args[2]
        if len(args) >= 4:
            score = args[3]
        if len(args) >= 5:
            max_score = args[4]

    # defaults
    cid = str(id or "UNKNOWN")
    ttl = str(title or cid)
    sev = str(severity or "INFO").upper()

    # normalize numeric
    try:
        sc = int(score)
    except Exception:
        sc = 0
    try:
        mx = int(max_score)
    except Exception:
        mx = 0

    if passed is None:
        ok = (sc == mx)
    else:
        ok = bool(passed)

    if evidence is None:
        evidence = {}

    return {
        "id": cid,
        "title": ttl,
        "severity": sev,
        "score": sc,
        "max_score": mx,
        "passed": ok,
        "what_failed": what_failed if not ok else "",
        "how_to_fix": how_to_fix if not ok else "",
        "evidence": evidence,
    }