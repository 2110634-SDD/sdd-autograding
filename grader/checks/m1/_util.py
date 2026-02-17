# grader/checks/m1/_util.py
from __future__ import annotations

from typing import Any, Dict, Optional


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

    2) Legacy positional style (kept for compatibility with existing checks):
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
    id = str(id or "UNKNOWN")
    title = str(title or id)
    severity = str(severity or "INFO").upper()

    # normalize numeric
    try:
        score_i = int(score)
    except Exception:
        score_i = 0
    try:
        max_i = int(max_score)
    except Exception:
        max_i = 0

    if passed is None:
        passed_b = (score_i == max_i)
    else:
        passed_b = bool(passed)

    # If failed but what_failed empty, allow caller to still pass a comment later;
    # keep empty by default.
    if evidence is None:
        evidence = {}

    return {
        "id": id,
        "title": title,
        "severity": severity,
        "score": score_i,
        "max_score": max_i,
        "passed": passed_b,
        "what_failed": what_failed if not passed_b else "",
        "how_to_fix": how_to_fix if not passed_b else "",
        "evidence": evidence,
    }


def evidence_path(path: str, exists: bool) -> Dict[str, Any]:
    """
    Small helper to standardize evidence about file existence.
    """
    return {
        "path": path,
        "text": f"{path} exists={exists}",
    }