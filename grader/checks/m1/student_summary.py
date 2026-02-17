# grader/checks/m1/student_summary.py
from __future__ import annotations

import re
from ._util import repo, read_text, item, evidence_path

PATH = "milestone1/STUDENT_SUMMARY.md"


def _count_ellipsis_lines(text: str) -> int:
    return len(re.findall(r"^\s*>\s*…\s*$", text, flags=re.MULTILINE))


def run_all(ctx):
    r = repo(ctx)
    p = r / PATH
    out = []

    # SUMMARY.01 exists
    if not p.exists():
        out.append(item("M1.SUMMARY.01","STUDENT_SUMMARY.md exists","BLOCKER",0,1,"ไม่พบ milestone1/STUDENT_SUMMARY.md",["สร้างไฟล์จาก template แล้วกรอกให้ครบ"],evidence={**evidence_path(PATH, False)}))
        # เหลือให้ fail แบบอธิบายสั้น
        out.append(item("M1.SUMMARY.02","Problem & Scope filled","MAJOR",0,3,"ไม่พบไฟล์ จึงตรวจไม่ได้",["สร้างไฟล์ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.SUMMARY.03","Out of scope provided","MAJOR",0,2,"ไม่พบไฟล์ จึงตรวจไม่ได้",["สร้างไฟล์ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.SUMMARY.04","Key Use Cases filled (UC1+UC2)","MAJOR",0,3,"ไม่พบไฟล์ จึงตรวจไม่ได้",["สร้างไฟล์ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.SUMMARY.05","Quality Attribute Drivers filled + trade-off","MAJOR",0,2,"ไม่พบไฟล์ จึงตรวจไม่ได้",["สร้างไฟล์ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.SUMMARY.06","Open questions / risks list ≥ 2","MINOR",0,1,"ไม่พบไฟล์ จึงตรวจไม่ได้",["สร้างไฟล์ก่อน"],evidence={**evidence_path(PATH, False)}))
        return out

    out.append(item("M1.SUMMARY.01","STUDENT_SUMMARY.md exists","BLOCKER",1,1,evidence={**evidence_path(PATH, True)}))
    text = read_text(p)

    # SUMMARY.02 section 1 no ellipsis (≥2 occurrences)
    sec1 = re.search(r"##\s*1\..*?(?=##\s*2\.)", text, flags=re.DOTALL)
    sec1_text = sec1.group(0) if sec1 else ""
    ell = _count_ellipsis_lines(sec1_text)
    ok2 = (ell == 0)
    out.append(item(
        item_id="M1.SUMMARY.02",
        title="Problem & Scope filled (no ellipsis placeholders)",
        severity="MAJOR",
        score=3 if ok2 else 0,
        max_score=3,
        what_failed="Section 1 ยังมี '> …' placeholder" if not ok2 else "",
        how_to_fix=["แทนที่ '> …' ในหัวข้อ 1 ด้วยเนื้อหาจริงอย่างน้อย 2 จุด"] if not ok2 else [],
        evidence={**evidence_path(PATH, True), "ellipsis_lines_in_section1": ell},
    ))

    # SUMMARY.03 out of scope non-empty
    out_scope = re.search(r"\*\*ขอบเขตที่ไม่ครอบคลุม.*?\*\*([\s\S]*?)(?=\n---|\n##\s*2\.|\Z)", text)
    out_txt = (out_scope.group(1) if out_scope else "").strip()
    ok3 = bool(out_txt) and ("> …" not in out_txt)
    out.append(item(
        item_id="M1.SUMMARY.03",
        title="Out of scope provided",
        severity="MAJOR",
        score=2 if ok3 else 0,
        max_score=2,
        what_failed="Out of scope ยังว่าง/ยังเป็น placeholder" if not ok3 else "",
        how_to_fix=["ใส่รายการ Out of scope อย่างน้อย 1 ข้อ (เป็น bullet/ข้อความจริง)"] if not ok3 else [],
        evidence={**evidence_path(PATH, True), "out_of_scope_nonempty": ok3},
    ))

    # SUMMARY.04 UC1/UC2 names not placeholder + reason non-empty (lightweight)
    uc1_ph = bool(re.search(r"\*\*Use Case 1:\*\*\s*`?<ชื่อ use case>`?", text))
    uc2_ph = bool(re.search(r"\*\*Use Case 2:\*\*\s*`?<ชื่อ use case>`?", text))
    ok4 = (not uc1_ph) and (not uc2_ph)
    out.append(item(
        item_id="M1.SUMMARY.04",
        title="Key Use Cases filled (UC1+UC2)",
        severity="MAJOR",
        score=3 if ok4 else 0,
        max_score=3,
        what_failed="Use Case 1/2 ยังเป็น placeholder" if not ok4 else "",
        how_to_fix=["แทน <ชื่อ use case> ด้วยชื่อจริงสำหรับ UC1 และ UC2"] if not ok4 else [],
        evidence={**evidence_path(PATH, True), "uc1_placeholder": uc1_ph, "uc2_placeholder": uc2_ph},
    ))

    # SUMMARY.05 QA driver + trade-off
    qa_ph = bool(re.search(r"\*\*Quality Attribute 1:\*\*\s*`?<ชื่อ quality attribute>`?", text))
    trade = bool(re.search(r"Trade-off.*?:\s*\S+", text))
    ok5 = (not qa_ph) and trade
    out.append(item(
        item_id="M1.SUMMARY.05",
        title="Quality Attribute Drivers filled + trade-off",
        severity="MAJOR",
        score=2 if ok5 else 0,
        max_score=2,
        what_failed="QA driver หรือ Trade-off ยังไม่ถูกกรอก" if not ok5 else "",
        how_to_fix=["ใส่ชื่อ QA จริง และเขียน Trade-off ให้มีเนื้อหา"] if not ok5 else [],
        evidence={**evidence_path(PATH, True), "qa_placeholder": qa_ph, "has_tradeoff": trade},
    ))

    # SUMMARY.06 open questions bullets >=2 (soft)
    oq = re.search(r"ประเด็นหรือความเสี่ยง.*?\n([\s\S]*?)(?=\n---|\Z)", text)
    oq_block = oq.group(1) if oq else ""
    bullets = [ln for ln in oq_block.splitlines() if ln.strip().startswith("-")]
    ok6 = len(bullets) >= 2
    out.append(item(
        item_id="M1.SUMMARY.06",
        title="Open questions / risks list ≥ 2",
        severity="MINOR",
        score=1 if ok6 else 0,
        max_score=1,
        what_failed="Open questions/risks น้อยกว่า 2 bullet" if not ok6 else "",
        how_to_fix=["เพิ่ม bullet อย่างน้อย 2 ข้อในหัวข้อประเด็น/ความเสี่ยง"] if not ok6 else [],
        evidence={**evidence_path(PATH, True), "bullet_count": len(bullets)},
    ))

    return out