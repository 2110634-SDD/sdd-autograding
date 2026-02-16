# grader/checks/m1/uc_fully_dressed_sections.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import re
from grader.core.models import Severity
from grader.utils_fs import read_text
from grader.utils_md import find_heading_blocks, canonicalize_heading, has_numbered_list, has_alt_exception_token
from grader.checks.m1.common import ok, fail, msg
from grader.checks.m1.uc_inventory import list_uc_files


REQUIRED_CANON = [
    "primary actor",
    "secondary actors",
    "goal",
    "preconditions",
    "main flow",
    "alternate / exception flows",
    "postconditions",
]

# Accept alternative spelling: "alternative / exception flows"
ALT_FLOW_ACCEPT = {"alternate / exception flows", "alternative / exception flows"}


def _canonical_map(headings: List[str]) -> Dict[str, str]:
    # canon -> original heading title
    out = {}
    for h in headings:
        c = canonicalize_heading(h)
        if c == "alternative / exception flows":
            out["alternate / exception flows"] = h
        else:
            out[c] = h
    return out


def check_uc_required_sections(repo: Path):
    check_id = "M1.UC.SECTION.01"
    title = "Required UC sections present (per file)"
    possible = 4  # capped total
    ucs = list_uc_files(repo)
    if not ucs:
        return fail(
            check_id, title, 0, possible,
            [msg(Severity.BLOCKER, "No UC files found", "Need UC files to validate fully dressed sections.",
                 ["Add UC01-...md and UC02-...md under milestone1/use-case-descriptions/."],
                 evidence="milestone1/use-case-descriptions/")],
        )

    per_file_missing: Dict[str, List[str]] = {}
    for p in ucs:
        md = read_text(p)
        blocks = find_heading_blocks(md)
        cmap = _canonical_map(list(blocks.keys()))

        missing = []
        for req in REQUIRED_CANON:
            if req == "alternate / exception flows":
                # already mapped to "alternate / exception flows"
                if "alternate / exception flows" not in cmap:
                    missing.append("## Alternate / Exception Flows")
            else:
                if req not in cmap:
                    # restore expected display
                    missing.append(f"## {req.title()}")
        if missing:
            per_file_missing[p.name] = missing

    if not per_file_missing:
        return ok(check_id, title, possible)

    # Score: if any file missing sections => 0 (strict) or partial (soft).
    # I suggest partial: earned=1 if only 1 file has small missing; but capped.
    # We'll do simple: earned = max(0, possible - len(per_file_missing))
    earned = max(0, possible - len(per_file_missing))
    msgs = []
    for fname, miss in per_file_missing.items():
        sev = Severity.BLOCKER if len(miss) >= 2 else Severity.MAJOR
        msgs.append(msg(
            sev,
            f"{fname} missing required section(s): {', '.join(miss)}",
            "Fully dressed use case ต้องมีหัวข้อหลักครบเพื่อใช้ต่อใน Milestone ถัดไป",
            ["Add the missing section headings exactly as in the template.",
             "Fill each section with concise content (not placeholder)."],
            evidence=f"milestone1/use-case-descriptions/{fname}",
        ))

    return fail(check_id, title, earned, possible, msgs, debug={"missing_by_file": per_file_missing})


def check_uc_minimum_content(repo: Path):
    check_id = "M1.UC.MIN.01"
    title = "Minimum content signals (Main Flow + Alt/Exception + Primary Actor)"
    possible = 2
    ucs = list_uc_files(repo)
    if not ucs:
        return fail(check_id, title, 0, possible,
                    [msg(Severity.MAJOR, "No UC files found", "Cannot validate minimum content.", ["Add at least 2 UC files."],
                         evidence="milestone1/use-case-descriptions/")])

    bad = {}
    for p in ucs:
        md = read_text(p)
        blocks = find_heading_blocks(md)
        cmap = _canonical_map(list(blocks.keys()))
        issues = []

        # Primary Actor non-empty
        pa_key = cmap.get("primary actor")
        if not pa_key or not blocks.get(pa_key, "").strip():
            issues.append("Primary Actor is empty")

        # Main Flow numbered list
        mf_key = cmap.get("main flow")
        if not mf_key or not has_numbered_list(blocks.get(mf_key, "")):
            issues.append("Main Flow has no numbered steps (e.g., '1.')")

        # Alt/Exception has A1./E1.
        alt_key = cmap.get("alternate / exception flows")
        if not alt_key or not has_alt_exception_token(blocks.get(alt_key, "")):
            issues.append("Alternate/Exception Flows missing A1./E1. entry")

        if issues:
            bad[p.name] = issues

    if not bad:
        return ok(check_id, title, possible)

    # soft: partial credit if only some files fail
    earned = 1 if len(bad) < len(ucs) else 0
    msgs = []
    for fname, issues in bad.items():
        msgs.append(msg(
            Severity.MAJOR,
            f"{fname} minimum content missing: {', '.join(issues)}",
            "หัวข้อครบอย่างเดียวไม่พอ ต้องมีสัญญาณขั้นต่ำว่ามี flow จริง",
            ["In Main Flow, add steps starting with '1.' '2.' ...",
             "In Alternate/Exception, add at least one 'A1.' or 'E1.' entry.",
             "Ensure Primary Actor is a single concrete actor."],
            evidence=f"milestone1/use-case-descriptions/{fname}",
        ))
    return fail(check_id, title, earned, possible, msgs, debug={"bad": bad})
