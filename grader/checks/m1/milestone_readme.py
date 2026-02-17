# grader/checks/m1/milestone_readme.py
from __future__ import annotations

import re
from ._util import repo, read_text, item, evidence_path

README_PATH = "milestone1/README.md"

PLACEHOLDER_REGEX = [
    r"\[Student Fill In\]",
    r"\(อธิบายปัญหาโดยสรุป 2–3 บรรทัด\)",
    r"-\s*\(อธิบายปัญหา",  # bullet placeholder
]


def run_all(ctx):
    r = repo(ctx)
    p = r / README_PATH
    out = []

    # README.01 exists
    if p.exists():
        out.append(item(
            item_id="M1.README.01",
            title="milestone1/README.md exists",
            severity="BLOCKER",
            score=1, max_score=1,
            evidence={**evidence_path(README_PATH, True)},
        ))
    else:
        out.append(item(
            item_id="M1.README.01",
            title="milestone1/README.md exists",
            severity="BLOCKER",
            score=0, max_score=1,
            what_failed="ไม่พบ milestone1/README.md",
            how_to_fix=["สร้าง milestone1/README.md จาก template แล้วกรอกให้ครบ"],
            evidence={**evidence_path(README_PATH, False)},
        ))
        # ถ้าไม่มีไฟล์ ก็ให้ตัวอื่น fail ตามไปแบบอธิบายสั้น ๆ
        out.append(item("M1.README.02","Overview section present","MAJOR",0,1,"ไม่พบ README.md จึงตรวจ Overview ไม่ได้",["สร้าง README.md ก่อน"],evidence={**evidence_path(README_PATH, False)}))
        out.append(item("M1.README.03","No [Student Fill In] remaining","MAJOR",0,3,"ไม่พบ README.md จึงตรวจ placeholder ไม่ได้",["สร้าง README.md ก่อน"],evidence={**evidence_path(README_PATH, False)}))
        out.append(item("M1.README.04","Placeholder bullets replaced","MAJOR",0,3,"ไม่พบ README.md จึงตรวจ placeholder ไม่ได้",["สร้าง README.md ก่อน"],evidence={**evidence_path(README_PATH, False)}))
        return out

    text = read_text(p)

    # README.02 overview
    has_overview = ("## Overview" in text)
    out.append(item(
        item_id="M1.README.02",
        title="Overview section present",
        severity="MAJOR",
        score=1 if has_overview else 0,
        max_score=1,
        what_failed="ไม่มีหัวข้อ ## Overview" if not has_overview else "",
        how_to_fix=["เพิ่มหัวข้อ ## Overview และสรุป 2–4 บรรทัด"] if not has_overview else [],
        evidence={**evidence_path(README_PATH, True), "has_overview": has_overview},
    ))

    # README.03 no [Student Fill In]
    has_fillin = ("[Student Fill In]" in text)
    out.append(item(
        item_id="M1.README.03",
        title="No [Student Fill In] remaining",
        severity="MAJOR",
        score=0 if has_fillin else 3,
        max_score=3,
        what_failed="ยังมี [Student Fill In] ค้างอยู่" if has_fillin else "",
        how_to_fix=["ค้นหา [Student Fill In] แล้วเติม/ลบให้หมด"] if has_fillin else [],
        evidence={**evidence_path(README_PATH, True), "has_student_fill_in": has_fillin},
    ))

    # README.04 placeholder bullets replaced
    hits = []
    for rx in PLACEHOLDER_REGEX[1:]:
        if re.search(rx, text):
            hits.append(rx)
    out.append(item(
        item_id="M1.README.04",
        title="Placeholder bullets replaced",
        severity="MAJOR",
        score=3 if not hits else 0,
        max_score=3,
        what_failed="ยังมี placeholder ที่ต้องแทนด้วยเนื้อหาจริง" if hits else "",
        how_to_fix=["ลบ/แทน placeholder ด้วยคำอธิบายจริง"] if hits else [],
        evidence={**evidence_path(README_PATH, True), "placeholder_regex_hits": hits},
    ))

    return out