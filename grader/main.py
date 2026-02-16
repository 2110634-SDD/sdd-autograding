# grader/main.py
from grader.core.context import GradingContext
from grader.checks.m0 import (
    team_file_exists,
    team_file_content,
    commit_contribution,
)

from grader.checks.m1 import (
    instructions_exists,
    instructions_anchors,
    manifest_core,
    readme_overview_filled,
    summary_minimums,
    uc_package,
)

# Mapping per milestone เพื่อรองรับอนาคต
CHECKSETS = {
    "M0": [
        ("team_file.exists", team_file_exists),
        ("team_file.content", team_file_content),
        ("commit.contribution", commit_contribution),
    ],
    "M1": [
        ("m1.contract.exists", instructions_exists),
        ("m1.contract.anchors", instructions_anchors),
        ("m1.manifest.core", manifest_core),
        ("m1.readme.overview", readme_overview_filled),
        ("m1.summary.minimums", summary_minimums),
        ("m1.uc.package", uc_package),
    ],
}


def _split_comment(comment: str):
    """
    Best-effort: แยก comment แบบไทยที่มักมีตัวคั่น เช่น
    "... | วิธีแก้: ... | บรรทัดที่ต้องแก้: ..."
    """
    s = (comment or "").strip()
    what = s
    how = ""
    ev = ""

    # แยก "วิธีแก้"
    if "วิธีแก้:" in s:
        before, after = s.split("วิธีแก้:", 1)
        what = before.strip(" |")
        how = after.strip()

    # แยก "บรรทัดที่ต้องแก้"
    if "บรรทัดที่ต้องแก้:" in s:
        before, after = s.split("บรรทัดที่ต้องแก้:", 1)
        # what/have may already be split; keep best
        what = before.strip(" |")
        ev = after.strip()

    return what, how, ev


def _normalize_item(check_id: str, raw, *, default_severity: str = "INFO"):
    """
    Normalize output into a renderer-friendly item schema:
      {
        id, title, severity, score, max_score, passed,
        what_failed, how_to_fix, evidence,
        comment (legacy, optional)
      }

    Accept:
      - dict (new style)
      - tuple(score, max_score, comment) (legacy)
    """
    # New style dict
    if isinstance(raw, dict):
        item = dict(raw)
        item.setdefault("id", check_id)
        item.setdefault("title", check_id)
        item.setdefault("severity", default_severity)

        # normalize score keys
        if "max_score" not in item and "max" in item:
            item["max_score"] = item["max"]
        if "score" not in item:
            item["score"] = 0
        if "max_score" not in item:
            item["max_score"] = 0

        score = item.get("score", 0)
        max_score = item.get("max_score", 0)

        # normalize passed
        if "passed" not in item:
            item["passed"] = (max_score <= 0) or (score >= max_score)

        # legacy comment fallback
        comment = str(item.get("comment", "") or "")
        if not item.get("what_failed") and comment:
            what, how, ev = _split_comment(comment)
            item.setdefault("what_failed", what)
            item.setdefault("how_to_fix", how)
            item.setdefault("evidence", ev)

        return item

    # Legacy tuple
    if not isinstance(raw, tuple) or len(raw) != 3:
        # system error schema
        return {
            "id": check_id,
            "title": check_id,
            "severity": "BLOCKER",
            "score": 0,
            "max_score": 0,
            "passed": False,
            "what_failed": f"[SYSTEM ERROR] invalid return from check: {raw}",
            "how_to_fix": "ผู้สอน: ตรวจระบบ autograder/check implementation",
            "evidence": "",
            "comment": str(raw),
        }

    score, max_score, comment = raw
    if not isinstance(score, (int, float)) or not isinstance(max_score, (int, float)):
        return {
            "id": check_id,
            "title": check_id,
            "severity": "BLOCKER",
            "score": 0,
            "max_score": 0,
            "passed": False,
            "what_failed": f"[SYSTEM ERROR] score/max_score not numeric: score={score}, max={max_score}",
            "how_to_fix": "ผู้สอน: ตรวจระบบ autograder/check implementation",
            "evidence": "",
            "comment": str(comment),
        }

    comment_s = str(comment)
    passed = (max_score <= 0) or (score >= max_score)

    # default severity: INFO if passed; MAJOR if failed (unless overridden later)
    severity = default_severity
    if not passed and severity == "INFO":
        severity = "MAJOR"

    what, how, ev = _split_comment(comment_s)

    return {
        "id": check_id,
        "title": check_id,
        "severity": severity,
        "score": score,
        "max_score": max_score,
        "passed": passed,
        "what_failed": "" if passed else what,
        "how_to_fix": "" if passed else how,
        "evidence": "" if passed else ev,
        "comment": comment_s,  # keep legacy
    }


def _safe_run_check(check_id, check, ctx):
    """
    Run a single check safely.
    Never raises.
    Accepts:
      - legacy tuple: (score, max_score, comment)
      - new dict item schema
    """
    try:
        # checks are modules with .run(ctx)
        raw = check.run(ctx)

        # If dict, accept
        if isinstance(raw, dict):
            return raw

        # If tuple, accept
        if isinstance(raw, tuple) and len(raw) == 3:
            score, max_score, _ = raw
            if isinstance(score, (int, float)) and isinstance(max_score, (int, float)):
                if max_score < 0 or score < 0 or score > max_score:
                    raise ValueError(f"invalid score values: score={score}, max_score={max_score}")
            return raw

        raise ValueError(f"check.run() must return dict or (score,max_score,comment), got {raw}")

    except Exception as e:
        return {
            "id": check_id,
            "title": check_id,
            "severity": "BLOCKER",
            "score": 0,
            "max_score": 0,
            "passed": False,
            "what_failed": f"[SYSTEM ERROR] Check '{check_id}' failed to run: {e}",
            "how_to_fix": "ผู้สอน: ตรวจระบบ autograder/check implementation",
            "evidence": "",
            "comment": f"[SYSTEM ERROR] {e}",
        }


def main():
    ctx = GradingContext.from_env()

    checks = CHECKSETS.get(ctx.milestone)
    if not checks:
        ctx.write_result(
            milestone=ctx.milestone,
            total=0,
            max=0,
            items=[
                {
                    "id": "milestone.unsupported",
                    "title": "Unsupported milestone",
                    "severity": "BLOCKER",
                    "score": 0,
                    "max_score": 0,
                    "passed": False,
                    "what_failed": f"Unsupported milestone '{ctx.milestone}'.",
                    "how_to_fix": "ผู้สอน: ตรวจ assignment/workflow configuration",
                    "evidence": "",
                    "comment": f"Unsupported milestone '{ctx.milestone}'.",
                }
            ],
        )
        return

    items = []
    total = 0
    max_total = 0

    for check_id, check in checks:
        raw = _safe_run_check(check_id, check, ctx)

        # per-check default severity policy (can evolve)
        default_sev = "INFO"
        if check_id == "commit.contribution":
            default_sev = "MAJOR"

        item = _normalize_item(check_id, raw, default_severity=default_sev)

        items.append(item)
        total += float(item.get("score", 0) or 0)
        max_total += float(item.get("max_score", 0) or 0)

    ctx.write_result(
        milestone=ctx.milestone,
        total=total,
        max=max_total,
        items=items,
    )


if __name__ == "__main__":
    main()