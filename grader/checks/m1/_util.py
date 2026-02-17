# grader/checks/m1/_util.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from grader.core.context import GradingContext


# -----------------------------
# Repo / file helpers
# -----------------------------
def repo(ctx: GradingContext) -> Path:
    return Path(ctx.repo_path)


def read_text(path: Path, *, default: str = "", encoding: str = "utf-8") -> str:
    try:
        return path.read_text(encoding=encoding)
    except Exception:
        return default


# -----------------------------
# Evidence helpers
# -----------------------------
def evidence_path(path: str, exists: bool) -> Dict[str, Any]:
    return {"path": path, "text": f"{path} exists={exists}"}


def evidence_text(path: str, text: str, *, line: Optional[int] = None, col: Optional[int] = None) -> Dict[str, Any]:
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
    # --- Aliases / compat ---
    item_id: Optional[str] = None,  # alias for id (some checks use item_id=...)
    max: Optional[int] = None,       # alias for max_score (legacy)
    # --- Canonical fields ---
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

    Supports:
      - keyword style using canonical args
      - keyword aliases: item_id -> id, max -> max_score
      - positional legacy style:
          item("ID", "Title", "BLOCKER", 0, 1, evidence=...)
    """
    # aliases
    if id is None and item_id is not None:
        id = item_id
    if max is not None and (max_score is None or max_score == 0):
        # only override if caller didn't set max_score explicitly
        max_score = max

    # positional legacy mapping
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

    cid = str(id or "UNKNOWN")
    ttl = str(title or cid)
    sev = str(severity or "INFO").upper()

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