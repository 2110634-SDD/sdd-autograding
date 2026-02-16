# tools/render_summary.py
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple


SEV_ORDER = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3, "UNKNOWN": 9}
SEV_TO_ANNOT = {"BLOCKER": "error", "MAJOR": "warning", "MINOR": "notice", "INFO": "notice", "UNKNOWN": "warning"}


def _get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _as_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)


def _norm_sev(x: Any) -> str:
    s = _as_str(x).strip().upper()
    if s in ("BLOCKER", "MAJOR", "MINOR", "INFO"):
        return s
    return "UNKNOWN"


def _status_bool(check: Dict[str, Any]) -> Optional[bool]:
    # Try common patterns
    for k in ("passed", "pass", "ok", "success"):
        if k in check and isinstance(check[k], bool):
            return check[k]
    status = _as_str(_get(check, "status", "result", default="")).lower()
    if status in ("pass", "passed", "ok", "success", "green"):
        return True
    if status in ("fail", "failed", "error", "red"):
        return False
    return None


def _score_pair(check: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    score = _get(check, "score", "points", default=None)
    max_score = _get(check, "max_score", "max", "out_of", default=None)
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None
    try:
        max_f = float(max_score) if max_score is not None else None
    except Exception:
        max_f = None
    return score_f, max_f


def _evidence_to_file_line(ev: Any) -> Tuple[str, Optional[int]]:
    # Evidence may be string or dict {path,line}
    if isinstance(ev, dict):
        path = _as_str(_get(ev, "path", "file", "filepath", default="")).strip()
        line = _get(ev, "line", "lineno", default=None)
        try:
            line_i = int(line) if line is not None else None
        except Exception:
            line_i = None
        return path, line_i
    # If string looks like "path:line" best-effort
    s = _as_str(ev).strip()
    if ":" in s:
        head, tail = s.rsplit(":", 1)
        try:
            line_i = int(tail)
            return head, line_i
        except Exception:
            pass
    return s, None


def _extract_checks(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Try common containers
    for k in ("checks", "items", "results", "details"):
        v = result.get(k)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
    # Some schemas nest under "report"
    rep = result.get("report")
    if isinstance(rep, dict):
        for k in ("checks", "items", "results"):
            v = rep.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def render(result: Dict[str, Any], milestone: str, submission_ref: str, submission_tag: str) -> Tuple[str, str]:
    checks = _extract_checks(result)

    # total score
    total_score = _get(result, "total_score", "score_total", default=None)
    total_max = _get(result, "max_score", "score_max", "total_max", default=None)

    try:
        total_score_f = float(total_score) if total_score is not None else None
    except Exception:
        total_score_f = None
    try:
        total_max_f = float(total_max) if total_max is not None else None
    except Exception:
        total_max_f = None

    # compute from checks if missing
    if total_score_f is None or total_max_f is None:
        ssum = 0.0
        msum = 0.0
        any_scores = False
        for c in checks:
            s, m = _score_pair(c)
            if s is not None and m is not None:
                any_scores = True
                ssum += s
                msum += m
        if any_scores:
            total_score_f = total_score_f if total_score_f is not None else ssum
            total_max_f = total_max_f if total_max_f is not None else msum

    # classify checks
    failed: List[Dict[str, Any]] = []
    passed_cnt = 0
    sev_counts = {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0, "UNKNOWN": 0}

    for c in checks:
        sev = _norm_sev(_get(c, "severity", "level", default="UNKNOWN"))
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

        pb = _status_bool(c)
        if pb is True:
            passed_cnt += 1
        elif pb is False:
            failed.append(c)
        else:
            # Unknown status: treat as failed if score < max
            s, m = _score_pair(c)
            if s is not None and m is not None and s < m:
                failed.append(c)

    # sort failed by severity then id
    def _sort_key(c: Dict[str, Any]):
        sev = _norm_sev(_get(c, "severity", "level", default="UNKNOWN"))
        cid = _as_str(_get(c, "id", "check_id", "code", default=""))
        return (SEV_ORDER.get(sev, 9), cid)

    failed.sort(key=_sort_key)

    # Decide pass/fail: if result explicitly has status, respect it; else fail if any BLOCKER failed
    explicit_status = _as_str(_get(result, "status", "result", default="")).upper()
    if explicit_status in ("PASS", "PASSED", "OK", "SUCCESS"):
        overall = "PASS"
    elif explicit_status in ("FAIL", "FAILED", "ERROR"):
        overall = "FAIL"
    else:
        # policy for now: FAIL if any failed BLOCKER
        any_blocker_fail = any(_norm_sev(_get(c, "severity", "level", default="UNKNOWN")) == "BLOCKER" for c in failed)
        overall = "FAIL" if any_blocker_fail else "PASS"

    # Prepare "Action Now" = top 3 failed (blocker first)
    action_now = failed[:3]

    # Markdown summary
    score_line = ""
    if total_score_f is not None and total_max_f is not None and total_max_f > 0:
        score_line = f"**Score:** {total_score_f:.0f}/{total_max_f:.0f}"
    elif total_score_f is not None:
        score_line = f"**Score:** {total_score_f:.0f}"
    else:
        score_line = "**Score:** (not provided)"

    tag_show = submission_tag if submission_tag else "(not a tag run)"
    ref_show = submission_ref if submission_ref else "(unknown)"

    md = []
    md.append(f"# Autograde Result — {milestone}")
    md.append("")
    md.append(f"- **Submission tag:** `{tag_show}`")
    md.append(f"- **Submission ref:** `{ref_show}`")
    md.append(f"- **Status:** **{overall}**")
    md.append(f"- {score_line}")
    md.append("")
    md.append(
        f"- **Failed checks:** {len(failed)} / **Passed checks:** {passed_cnt} / **Total checks:** {len(checks)}"
    )
    md.append(
        f"- **Severity counts:** BLOCKER={sev_counts.get('BLOCKER',0)}, MAJOR={sev_counts.get('MAJOR',0)}, MINOR={sev_counts.get('MINOR',0)}"
    )
    md.append("")

    if action_now:
        md.append("## Action Now (แก้ 1–3 อย่างนี้ก่อน)")
        md.append("")
        for c in action_now:
            cid = _as_str(_get(c, "id", "check_id", "code", default="(no id)"))
            title = _as_str(_get(c, "title", "name", default="")).strip()
            sev = _norm_sev(_get(c, "severity", "level", default="UNKNOWN"))
            what = _as_str(_get(c, "what_failed", "message", "summary", default="")).strip()
            how = _as_str(_get(c, "how_to_fix", "fix", "hint", default="")).strip()
            label = f"**{cid}**"
            if title:
                label += f" — {title}"
            line = f"- [{sev}] {label}: {what if what else 'Check failed'}"
            if how:
                line += f"  \n  ↳ **How to fix:** {how}"
            md.append(line)
        md.append("")

    md.append("## Failed checks")
    md.append("")
    if not failed:
        md.append("✅ ไม่มี failed checks")
    else:
        md.append("| ID | Severity | Score | What failed | How to fix | Evidence |")
        md.append("|---|---:|---:|---|---|---|")
        for c in failed:
            cid = _as_str(_get(c, "id", "check_id", "code", default="(no id)"))
            sev = _norm_sev(_get(c, "severity", "level", default="UNKNOWN"))
            s, m = _score_pair(c)
            score_cell = ""
            if s is not None and m is not None:
                score_cell = f"{int(s)}/{int(m)}"
            elif s is not None:
                score_cell = f"{int(s)}"
            else:
                score_cell = ""
            what = _as_str(_get(c, "what_failed", "message", "summary", default="")).replace("\n", " ").strip()
            how = _as_str(_get(c, "how_to_fix", "fix", "hint", default="")).replace("\n", " ").strip()
            ev = _get(c, "evidence", "evidences", default="")
            if isinstance(ev, list) and ev:
                ev0 = ev[0]
            else:
                ev0 = ev
            ev_path, ev_line = _evidence_to_file_line(ev0)
            ev_cell = ev_path
            if ev_line:
                ev_cell = f"{ev_path}:{ev_line}"
            md.append(f"| `{cid}` | {sev} | {score_cell} | {what} | {how} | `{ev_cell}` |")
    md.append("")
    md.append("## Notes")
    md.append("")
    md.append("- รายละเอียดเต็ม (JSON/Logs) ดูได้จาก artifact ของ run นี้")
    md.append("")

    summary_md = "\n".join(md)

    # Annotations text (printed to stdout in workflow)
    ann_lines: List[str] = []
    for c in failed:
        sev = _norm_sev(_get(c, "severity", "level", default="UNKNOWN"))
        atype = SEV_TO_ANNOT.get(sev, "warning")

        cid = _as_str(_get(c, "id", "check_id", "code", default="(no id)"))
        title = _as_str(_get(c, "title", "name", default="")).strip()

        what = _as_str(_get(c, "what_failed", "message", "summary", default="Check failed")).strip()
        how = _as_str(_get(c, "how_to_fix", "fix", "hint", default="")).strip()

        msg = f"[{cid}] {title + ' — ' if title else ''}{what}"
        if how:
            msg += f" | How to fix: {how}"

        ev = _get(c, "evidence", "evidences", default="")
        if isinstance(ev, list) and ev:
            ev0 = ev[0]
        else:
            ev0 = ev
        path, line = _evidence_to_file_line(ev0)

        # Only add file/line if path looks like a file in repo
        if path and ("/" in path or path.endswith(".md") or path.endswith(".png") or path.endswith(".puml") or path.endswith(".yml") or path.endswith(".yaml")):
            if line and line > 0:
                ann_lines.append(f"::{atype} file={path},line={line}::{msg}")
            else:
                ann_lines.append(f"::{atype} file={path}::{msg}")
        else:
            ann_lines.append(f"::{atype}::{msg}")

    annotations_txt = "\n".join(ann_lines) + ("\n" if ann_lines else "")
    return summary_md, annotations_txt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, help="Path to grading_result_*.json")
    ap.add_argument("--milestone", required=True, help="Milestone id เช่น M1")
    ap.add_argument("--submission-ref", default="", help="Submission ref (tag/sha/branch)")
    ap.add_argument("--submission-tag", default="", help="Submission tag if applicable")
    ap.add_argument("--summary-out", required=True, help="Output markdown path")
    ap.add_argument("--annotations-out", required=True, help="Output annotations text path")
    args = ap.parse_args()

    with open(args.result, "r", encoding="utf-8") as f:
        result = json.load(f)

    summary_md, annotations_txt = render(
        result=result,
        milestone=args.milestone,
        submission_ref=args.submission_ref,
        submission_tag=args.submission_tag,
    )

    os.makedirs(os.path.dirname(args.summary_out) or ".", exist_ok=True)
    with open(args.summary_out, "w", encoding="utf-8") as f:
        f.write(summary_md)

    os.makedirs(os.path.dirname(args.annotations_out) or ".", exist_ok=True)
    with open(args.annotations_out, "w", encoding="utf-8") as f:
        f.write(annotations_txt)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())