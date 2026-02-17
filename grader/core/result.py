# grader/core/result.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a check item into a stable schema for renderers.

    Expected canonical fields (from grader/checks/m1/_util.item()):
      id, title, severity, score, max_score, passed,
      what_failed, how_to_fix, evidence

    This function is backward-compatible:
      - supports aliases like max -> max_score
      - fills missing keys with safe defaults
      - coerces score/max_score to int
      - ensures evidence is either dict or list/dict/string normalized safely
    """
    # Work on a copy to avoid mutating caller data unexpectedly
    it: Dict[str, Any] = dict(item or {})

    # Backward-compatible aliases
    if "max_score" not in it and "max" in it:
        it["max_score"] = it["max"]

    # Required core fields with defaults
    it.setdefault("id", "UNKNOWN")
    it.setdefault("title", it.get("id", "UNKNOWN"))
    it.setdefault("severity", "INFO")  # prefer INFO over UNKNOWN for UI
    it.setdefault("score", 0)
    it.setdefault("max_score", 0)

    # Normalize numeric
    try:
        it["score"] = int(it.get("score", 0))
    except Exception:
        it["score"] = 0
    try:
        it["max_score"] = int(it.get("max_score", 0))
    except Exception:
        it["max_score"] = 0

    # Passed inference (only if missing)
    if "passed" not in it:
        it["passed"] = (it["score"] == it["max_score"])
    else:
        it["passed"] = bool(it.get("passed"))

    # UI fields: keep empty strings if passed; renderer can still show
    it.setdefault("what_failed", "" if it["passed"] else "")
    it.setdefault("how_to_fix", "" if it["passed"] else "")
    it.setdefault("evidence", {})

    # Legacy optional fields
    it.setdefault("comment", "")

    # Evidence normalization:
    # - allow dict / list / str / anything
    # - renderer handles dict/list/str; here we just make it safe
    ev = it.get("evidence")
    if ev is None:
        it["evidence"] = {}
    elif isinstance(ev, (dict, list, str)):
        # keep as-is
        pass
    else:
        # fallback: wrap unknown types into dict
        it["evidence"] = {"value": str(ev)}

    return it


@dataclass
class GradingResult:
    milestone: str
    items: List[Dict[str, Any]] = field(default_factory=list)

    # ---- Constructors ----
    @classmethod
    def from_items(cls, items: Iterable[Dict[str, Any]], milestone: str) -> "GradingResult":
        gr = cls(milestone=milestone)
        gr.extend(list(items or []))
        return gr

    # ---- Legacy API ----
    def add(self, item_id: str, score: int, max_score: int, comment: str = ""):
        """
        Legacy add: keep working.

        NOTE:
          - severity inference here is simplistic; prefer add_item_dict()
          - if failed, severity becomes BLOCKER to preserve previous behavior
        """
        passed = (int(score) == int(max_score))
        item = {
            "id": item_id,
            "title": item_id,
            "severity": "MINOR" if passed else "BLOCKER",
            "score": int(score),
            "max_score": int(max_score),
            "passed": passed,
            "comment": comment or "",
            "what_failed": "" if passed else (comment or ""),
            "how_to_fix": "" if passed else "",
            "evidence": {},
        }
        self.items.append(normalize_item(item))

    # ---- New API ----
    def add_item_dict(self, item: Dict[str, Any]):
        """
        New path: expects dict schema from checks (via _util.item()).
        We'll normalize to guarantee renderer stability.
        """
        self.items.append(normalize_item(item))

    def extend(self, items: List[Dict[str, Any]]):
        for it in items or []:
            self.add_item_dict(it)

    # ---- Aggregates ----
    @property
    def total_score(self) -> int:
        return int(sum(int(it.get("score", 0)) for it in self.items))

    @property
    def total_max_score(self) -> int:
        return int(sum(int(it.get("max_score", 0)) for it in self.items))

    @property
    def passed(self) -> bool:
        """
        Overall policy for job status:
          FAIL iff any BLOCKER failed
        """
        for it in self.items:
            if (not bool(it.get("passed", False))) and (str(it.get("severity", "")).upper() == "BLOCKER"):
                return False
        return True

    @property
    def summary_counts(self) -> Dict[str, int]:
        """
        Renderer-friendly counts.
        Keys used by tools/render_summary.py:
          passed, failed, blocker_failed
        Also provide totals for debugging/other UIs.
        """
        failed = [it for it in self.items if not bool(it.get("passed", False))]
        passed = [it for it in self.items if bool(it.get("passed", False))]
        blockers = [it for it in failed if str(it.get("severity", "")).upper() == "BLOCKER"]
        return {
            "total": len(self.items),
            "passed": len(passed),
            "failed": len(failed),
            "blocker_failed": len(blockers),
        }