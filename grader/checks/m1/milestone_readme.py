# grader/checks/m1/milestone_readme.py
from __future__ import annotations
from pathlib import Path
from grader.core.models import Severity
from grader.utils_fs import read_text
from grader.utils_md import contains_placeholder
from grader.checks.m1.common import ok, fail, msg


PLACEHOLDERS = [
    "[Student Fill In]",
    "(อธิบายปัญหาโดยสรุป 2–3 บรรทัด)",
]


def check_m1_readme_exists(repo: Path):
    check_id = "M1.README.01"
    title = "milestone1/README.md exists"
    possible = 1
    path = repo / "milestone1" / "README.md"
    if path.exists():
        return ok(check_id, title, possible)
    return fail(
        check_id, title, 0, possible,
        [msg(Severity.BLOCKER, "Missing milestone1/README.md", "README ใช้บอกผู้อ่านว่า artefacts อยู่ไหนและอ่านอย่างไร",
             ["Restore file from template and fill required sections."], str(path))],
    )


def check_m1_readme_overview_present(repo: Path):
    check_id = "M1.README.02"
    title = "Overview section present"
    possible = 1
    path = repo / "milestone1" / "README.md"
    if not path.exists():
        return fail(check_id, title, 0, possible,
                    [msg(Severity.MAJOR, "Cannot find README.md", "Need README to validate sections.", ["Create milestone1/README.md"], str(path))])

    text = read_text(path)
    if "## Overview" in text:
        return ok(check_id, title, possible)
    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR, "Missing '## Overview' section", "Overview เป็นส่วนที่ทีมต้องเติมเพื่อสรุปปัญหาและภาพรวมระบบ",
             ["Add section heading '## Overview' and describe the problem in 2–3 lines."], str(path))],
    )


def check_m1_readme_no_student_fill_in(repo: Path):
    check_id = "M1.README.03"
    title = "No [Student Fill In] remaining in README"
    possible = 3
    path = repo / "milestone1" / "README.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "README missing", "Cannot validate fill-in markers.", ["Create README.md"], str(path))])

    text = read_text(path)
    if "[Student Fill In]" not in text:
        return ok(check_id, title, possible)
    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR, "README still contains [Student Fill In]", "Template marker ต้องถูกแทนด้วยเนื้อหาจริง",
             ["Remove '[Student Fill In]' from the Overview heading.",
              "Replace placeholder bullets with your project summary (2–3 lines)."], str(path))],
    )


def check_m1_readme_placeholders_replaced(repo: Path):
    check_id = "M1.README.04"
    title = "README placeholder bullets replaced"
    possible = 3
    path = repo / "milestone1" / "README.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "README missing", "Cannot validate placeholders.", ["Create README.md"], str(path))])

    text = read_text(path)
    found = contains_placeholder(text, PLACEHOLDERS)
    if not found:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR, f"README still contains placeholders: {', '.join(found)}",
             "Placeholder หมายถึงทีมยังไม่ได้เติมคำอธิบายปัญหา/ผู้ใช้/เป้าหมายระบบ",
             ["Replace the placeholder lines with real content.",
              "Keep it short: 2–3 lines about the problem, primary users, and system goal."],
             str(path))],
        debug={"found_placeholders": found},
    )
