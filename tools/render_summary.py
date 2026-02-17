# tools/render_summary.py
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from grader.core.result import GradingResult


SEV_ORDER = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}
DEFAULT_EVIDENCE_MAX = 140


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _as_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[: max(0, n - 1)].rstrip() + "…"


def _md_escape(s: str) -> str:
    # minimal escape for table rendering
    return (s or "").replace("\n", "<br>").replace("|", "\\|")


def _severity(item: Dict[str, Any]) -> str:
    return (item.get("severity") or "INFO").upper()


def _score_str(item: Dict[str, Any]) -> str:
    score = item.get("score")
    max_score = item.get("max_score")
    try:
        if score is None and max_score is None:
            return "-"
        if max_score in (None, 0, "0"):
            return f"{score}"
        return f"{score}/{max_score}"
    except Exception:
        return f"{score}/{max_score}"


def _failed_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [it for it in items if not bool(it.get("passed"))]


def _overall_passed(items: Iterable[Dict[str, Any]]) -> bool:
    # FAIL iff any BLOCKER failed
    for it in items:
        if not bool(it.get("passed")) and _severity(it) == "BLOCKER":
            return False
    return True


def _annotation_level(severity: str) -> str:
    severity = (severity or "").upper()
    return "error" if severity == "BLOCKER" else "warning"


def _evidence_to_location(evidence: Any) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
    """
    Return (file, line, col, evidence_text).
    evidence may be:
      - str
      - dict {path, line, col, text, ...}
      - list of such
    """
    if isinstance(evidence, list) and evidence:
        for e in evidence:
            f, l, c, t = _evidence_to_location(e)
            if f or t:
                return f, l, c, t
        return None, None, None, ""

    if isinstance(evidence, dict):
        path = evidence.get("path") or evidence.get("file")
        line = evidence.get("line")
        col = evidence.get("col")
        text = evidence.get("text")
        if text is None:
            text = _as_str(evidence)
        return (
            path,
            int(line) if isinstance(line, int) else None,
            int(col) if isinstance(col, int) else None,
            _as_str(text),
        )

    return None, None, None, _as_str(evidence)


def _write_summary(md: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        # Not in GitHub Actions; fallback to stdout
        print(md)
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(md)
        if not md.endswith("\n"):
            f.write("\n")


def _emit_annotation(item: Dict[str, Any]) -> None:
    """
    GitHub Actions workflow command:
      ::error file=...,line=...,col=...::message
    """
    sev = _severity(item)
    level = _annotation_level(sev)

    cid = _as_str(item.get("id"))
    title = _as_str(item.get("title"))
    what_failed = _as_str(item.get("what_failed"))
    how_to_fix = _as_str(item.get("how_to_fix"))

    evidence = item.get("evidence")
    file, line, col, ev_text = _evidence_to_location(evidence)

    msg_core = f"[{cid}] {title} — {what_failed}".strip()
    if how_to_fix:
        msg_core += f" | Fix: {how_to_fix}"
    if ev_text:
        msg_core += f" | Evidence: {_truncate(ev_text, 160)}"

    # sanitize newlines for workflow commands
    msg_core = re.sub(r"[\r\n]+", " ", msg_core).strip()

    meta_parts = []
    if file:
        meta_parts.append(f"file={file}")
    if line:
        meta_parts.append(f"line={line}")
    if col:
        meta_parts.append(f"col={col}")
    meta = ",".join(meta_parts)

    if meta:
        print(f"::{level} {meta}::{msg_core}")
    else:
        print(f"::{level}::{msg_core}")


def render_to_github_actions(result: GradingResult, milestone: str) -> bool:
    """
    Writes:
      - Job Summary (GITHUB_STEP_SUMMARY)
      - Annotations (stdout workflow commands)
    Returns:
      overall_passed (FAIL if any BLOCKER failed)
    """
    items = list(getattr(result, "items", None) or [])
    overall = _overall_passed(items)

    failed = _failed_items(items)
    failed_sorted = sorted(
        failed,
        key=lambda it: (SEV_ORDER.get(_severity(it), 99), _as_str(it.get("id"))),
    )

    counts = getattr(result, "summary_counts", None) or {}
    passed_count = counts.get("passed", sum(1 for it in items if bool(it.get("passed"))))
    failed_count = counts.get("failed", len(items) - passed_count)
    blocker_failed = sum(1 for it in items if (not bool(it.get("passed"))) and _severity(it) == "BLOCKER")

    total_score = getattr(result, "total_score", None)
    total_max = getattr(result, "total_max_score", None)

    score_line = ""
    if total_score is not None or total_max is not None:
        score_line = f"- **Score:** {total_score}/{total_max}\n"

    status_emoji = "✅" if overall else "❌"

    md: List[str] = []
    md.append(f"# Autograde Result — {milestone}\n")
    md.append(f"- **Status:** {status_emoji} **{'PASS' if overall else 'FAIL'}**\n")
    md.append(f"- **Checks:** {passed_count} passed / {failed_count} failed (BLOCKER failed: {blocker_failed})\n")
    if score_line:
        md.append(score_line)
    md.append(f"- **Generated:** {_now_iso()}\n\n")

    if failed_sorted:
        md.append("## Failed checks\n\n")
        md.append(
            "| ID | Title | Severity | Score | What failed | How to fix | Evidence |\n"
            "|---|---|---:|---:|---|---|---|\n"
        )
        for it in failed_sorted:
            evid = it.get("evidence")
            _, _, _, ev_text = _evidence_to_location(evid)
            md.append(
                f"| `{_md_escape(_as_str(it.get('id')))}`"
                f" | {_md_escape(_as_str(it.get('title')))}"
                f" | **{_md_escape(_severity(it))}**"
                f" | `{_md_escape(_score_str(it))}`"
                f" | {_md_escape(_truncate(_as_str(it.get('what_failed')), 160))}"
                f" | {_md_escape(_truncate(_as_str(it.get('how_to_fix')), 160))}"
                f" | {_md_escape(_truncate(ev_text, DEFAULT_EVIDENCE_MAX))}"
                " |\n"
            )
        md.append("\n")
    else:
        md.append("## Failed checks\n\n- None 🎉\n\n")

    md.append("<details><summary>All checks</summary>\n\n")
    md.append("| ID | Severity | Status | Score | Title |\n|---|---:|---:|---:|---|\n")
    for it in sorted(items, key=lambda x: (SEV_ORDER.get(_severity(x), 99), _as_str(x.get("id")))):
        st = "PASS" if bool(it.get("passed")) else "FAIL"
        md.append(
            f"| `{_md_escape(_as_str(it.get('id')))}`"
            f" | {_md_escape(_severity(it))}"
            f" | **{st}**"
            f" | `{_md_escape(_score_str(it))}`"
            f" | {_md_escape(_as_str(it.get('title')))} |\n"
        )
    md.append("\n</details>\n")

    _write_summary("".join(md))

    for it in failed_sorted:
        _emit_annotation(it)

    return overall