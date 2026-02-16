# grader/checks/m1/student_summary.py
from __future__ import annotations
from pathlib import Path
import re
from grader.core.models import Severity
from grader.utils_fs import read_text
from grader.checks.m1.common import ok, fail, msg


def _count_placeholders(text: str) -> int:
    # template uses "> …" a lot
    return len(re.findall(r"^\s*>\s*…\s*$", text, flags=re.MULTILINE))


def check_summary_exists(repo: Path):
    check_id = "M1.SUMMARY.01"
    title = "STUDENT_SUMMARY.md exists"
    possible = 1
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if path.exists():
        return ok(check_id, title, possible)
    return fail(check_id, title, 0, possible,
                [msg(Severity.BLOCKER, "Missing STUDENT_SUMMARY.md", "ไฟล์นี้ใช้บอกเหตุผล (why) และ trade-offs",
                     ["Restore file from template and fill the sections."], str(path))])


def check_summary_problem_scope_filled(repo: Path):
    check_id = "M1.SUMMARY.02"
    title = "Problem & Scope filled (no ellipsis placeholders)"
    possible = 3
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "STUDENT_SUMMARY missing", "Cannot validate.", ["Create file."], str(path))])

    text = read_text(path)
    # focus section 1 only (lightweight): from heading "## 1." to next "## 2."
    m = re.search(r"##\s*1\..*?(?=##\s*2\.)", text, flags=re.DOTALL)
    sec = m.group(0) if m else text
    ph = _count_placeholders(sec)
    if ph == 0:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             f"Section 1 still contains {ph} placeholder line(s) ('> …')",
             "Section 1 ต้องอธิบายปัญหา, primary users และขอบเขตที่ไม่ทำ เพื่อให้ scope ชัด",
             ["Replace '> …' with your actual text for problem, users, and out-of-scope.",
              "Keep it concise but specific."],
             str(path))],
        debug={"placeholders_in_section1": ph},
    )


def check_summary_out_of_scope(repo: Path):
    check_id = "M1.SUMMARY.03"
    title = "Out of scope provided"
    possible = 2
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "Missing STUDENT_SUMMARY", "Cannot validate.", ["Create file."], str(path))])

    text = read_text(path)
    # locate Out of scope block
    m = re.search(r"\*\*ขอบเขตที่ไม่ครอบคลุม.*?\*\*([\s\S]*?)(?=\n---|\n##\s*2\.|\Z)", text)
    block = (m.group(1) if m else "").strip()
    if block and "> …" not in block:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             "Out of scope is missing or still placeholder",
             "M1 ต้องระบุอย่างน้อย 1 out-of-scope เพื่อกัน scope creep และใช้ต่อใน M2",
             ["Fill 'Out of scope' with at least 1 concrete item you will NOT build.",
              "Avoid implementation details; focus on capability/scope."],
             str(path))],
        debug={"out_of_scope_block": block[:200]},
    )


def check_summary_key_usecases(repo: Path):
    check_id = "M1.SUMMARY.04"
    title = "Key Use Cases filled (UC1+UC2)"
    possible = 3
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "Missing STUDENT_SUMMARY", "Cannot validate.", ["Create file."], str(path))])

    text = read_text(path)
    # Fail if placeholders remain in UC1 or UC2 titles
    bad = []
    for k in ("Use Case 1:", "Use Case 2:"):
        m = re.search(rf"\*\*{re.escape(k)}\*\*\s*`?<ชื่อ use case>`?", text)
        if m:
            bad.append(k)
    if not bad:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             f"Key Use Cases still contain placeholders: {', '.join(bad)}",
             "ต้องระบุ use case หลัก 2 อันและเหตุผล เพื่อยึดแกนของระบบใน M2",
             ["Replace '<ชื่อ use case>' with real use case names.",
              "Add 1–3 lines explaining why each is critical."],
             str(path))],
    )


def check_summary_qa_tradeoff(repo: Path):
    check_id = "M1.SUMMARY.05"
    title = "Quality Attribute Drivers filled + trade-off"
    possible = 2
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "Missing STUDENT_SUMMARY", "Cannot validate.", ["Create file."], str(path))])

    text = read_text(path)
    # simple heuristic: find at least one "Quality Attribute 1" block without placeholders and with "Trade-off" filled
    m = re.search(r"\*\*Quality Attribute 1:\*\*\s*`?<ชื่อ quality attribute>`?", text)
    if m:
        return fail(
            check_id, title, 0, possible,
            [msg(Severity.MAJOR,
                 "Quality Attribute 1 is still placeholder",
                 "ต้องระบุ QA driver อย่างน้อย 1 ตัว พร้อมเหตุผลและ trade-off เพื่อใช้กำหนดทิศทางใน M2",
                 ["Replace '<ชื่อ quality attribute>' with an actual attribute (e.g., Security, Usability).",
                  "Fill 'Trade-off ที่ยอมรับ' with at least one concrete trade-off."],
                 str(path))],
        )

    # trade-off filled?
    # accept if there is any non-placeholder content after 'Trade-off ที่ยอมรับ:' in QA1
    qa1 = re.search(r"\*\*Quality Attribute 1:.*?(?=\*\*Quality Attribute 2|\n##\s*4\.|\Z)", text, flags=re.DOTALL)
    block = qa1.group(0) if qa1 else ""
    trade = re.search(r"Trade-off.*?:\s*(.*)", block)
    if trade and trade.group(1).strip() and "…" not in trade.group(1):
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             "Trade-off in Quality Attribute Drivers is missing/empty",
             "Trade-off เป็นหัวใจของ design reasoning (why) และช่วยให้ TA/Autograde เห็นทิศทาง",
             ["Add at least 1 trade-off you accept (e.g., better security but slower login)."],
             str(path))],
        debug={"qa1_block_preview": block[:250]},
    )


def check_summary_open_questions(repo: Path):
    check_id = "M1.SUMMARY.06"
    title = "Open questions / risks list ≥ 2"
    possible = 1
    path = repo / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MINOR, "Missing STUDENT_SUMMARY", "Cannot validate.", ["Create file."], str(path))])

    text = read_text(path)
    m = re.search(r"ประเด็นหรือความเสี่ยง.*?\n([\s\S]*?)(?=\n---|\Z)", text)
    block = (m.group(1) if m else "")
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("-")]
    if len(bullets) >= 2:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MINOR,
             "Open questions / risks has fewer than 2 bullet points",
             "อย่างน้อย 2 ประเด็นช่วยชี้ว่า M2 ต้องพิสูจน์อะไรต่อ",
             ["Add 2–3 bullet points under 'ประเด็นหรือความเสี่ยงที่ต้องพิสูจน์ใน Milestone 2'."],
             str(path))],
        debug={"bullet_count": len(bullets)},
    )
