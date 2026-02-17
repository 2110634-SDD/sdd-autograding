# grader/checks/m1/uc_inventory.py
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set

from ._util import repo, read_text, item, evidence_path
from .uc_fully_dressed import _uc_files  # reuse helper


REQUIRED_HEADERS = {"Use Case ID", "Use Case Name", "Primary Actor", "File"}
PATH = "milestone1/use-case-descriptions/README.md"


def _parse_first_md_table(text: str):
    # very small parser: find first table block with |...|
    lines = [ln.rstrip() for ln in text.splitlines()]
    idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and "|" in ln.strip()[1:]:
            idx = i
            break
    if idx is None:
        return None
    # header line + separator + rows until non-table
    header = lines[idx]
    if idx + 1 >= len(lines):
        return None
    sep = lines[idx + 1]
    if "-" not in sep:
        return None
    def split_row(row: str):
        parts = [c.strip() for c in row.strip().strip("|").split("|")]
        return parts
    headers = split_row(header)
    rows = []
    j = idx + 2
    while j < len(lines):
        ln = lines[j]
        if not ln.strip().startswith("|"):
            break
        cells = split_row(ln)
        if len(cells) >= len(headers):
            rows.append(dict(zip(headers, cells)))
        j += 1
    return headers, rows


def run_all(ctx):
    r = repo(ctx)
    p = r / PATH
    out = []

    if not p.exists():
        out.append(item(
            item_id="M1.UC.PACK.01",
            title="use-case-descriptions/README.md exists",
            severity="BLOCKER",
            score=0, max_score=1,
            what_failed="ไม่พบ use-case-descriptions/README.md",
            how_to_fix=["Restore milestone1/use-case-descriptions/README.md จาก template แล้วกรอกตาราง inventory"],
            evidence={**evidence_path(PATH, False)},
        ))
        # downstream
        out.append(item("M1.UC.PACK.02","UC inventory table present with required headers","MAJOR",0,3,"ไม่พบ README จึงตรวจไม่ได้",["สร้าง README ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.UC.TABLE.01","Every UC file listed in UC README table","MAJOR",0,3,"ไม่พบ README จึงตรวจไม่ได้",["สร้าง README ก่อน"],evidence={**evidence_path(PATH, False)}))
        out.append(item("M1.UC.TABLE.02","UC README table does not contain placeholders","MINOR",0,2,"ไม่พบ README จึงตรวจไม่ได้",["สร้าง README ก่อน"],evidence={**evidence_path(PATH, False)}))
        return out

    out.append(item("M1.UC.PACK.01","use-case-descriptions/README.md exists","BLOCKER",1,1,evidence={**evidence_path(PATH, True)}))

    text = read_text(p)
    t = _parse_first_md_table(text)

    if not t:
        out.append(item(
            item_id="M1.UC.PACK.02",
            title="UC inventory table present with required headers",
            severity="MAJOR",
            score=0, max_score=3,
            what_failed="ไม่พบ markdown table ใน UC README",
            how_to_fix=["เพิ่มตาราง markdown ที่มี header: Use Case ID | Use Case Name | Primary Actor | File"],
            evidence={**evidence_path(PATH, True), "table_found": False},
        ))
        # table-based checks fail
        out.append(item("M1.UC.TABLE.01","Every UC file listed in UC README table","MAJOR",0,3,"ไม่มีตาราง จึง cross-check ไม่ได้",["เพิ่มตารางก่อน"],evidence={**evidence_path(PATH, True), "table_found": False}))
        out.append(item("M1.UC.TABLE.02","UC README table does not contain placeholders","MINOR",0,2,"ไม่มีตาราง จึงตรวจ placeholder ไม่ได้",["เพิ่มตารางก่อน"],evidence={**evidence_path(PATH, True), "table_found": False}))
        return out

    headers, rows = t
    missing_headers = sorted(list(REQUIRED_HEADERS - set(headers)))
    ok_headers = (len(missing_headers) == 0)
    out.append(item(
        item_id="M1.UC.PACK.02",
        title="UC inventory table present with required headers",
        severity="MAJOR",
        score=3 if ok_headers else 0,
        max_score=3,
        what_failed=f"ตารางขาด header: {missing_headers}" if not ok_headers else "",
        how_to_fix=["แก้ header ของตารางให้ครบ Use Case ID / Use Case Name / Primary Actor / File"] if not ok_headers else [],
        evidence={**evidence_path(PATH, True), "headers": headers, "missing_headers": missing_headers},
    ))

    # TABLE.02 placeholders
    ph_tokens = ["<ชื่อ use case>", "<actor>", "UC01-<name>.md", "UC02-<name>.md", "UC03-<name>.md"]
    found_ph = [tok for tok in ph_tokens if tok in text]
    out.append(item(
        item_id="M1.UC.TABLE.02",
        title="UC README table does not contain placeholders",
        severity="MINOR",
        score=2 if not found_ph else 0,
        max_score=2,
        what_failed=f"ยังมี placeholder ใน UC README: {found_ph}" if found_ph else "",
        how_to_fix=["แทน placeholder (<...>) ด้วยค่าจริง แล้วลบ placeholder ออก"] if found_ph else [],
        evidence={**evidence_path(PATH, True), "placeholders_found": found_ph},
    ))

    # TABLE.01 every UC file listed
    ucs = _uc_files(r)
    listed = set((row.get("File", "") or "").strip() for row in rows)
    missing_rows = [p.name for p in ucs if p.name not in listed]
    ok_listed = (len(missing_rows) == 0)
    out.append(item(
        item_id="M1.UC.TABLE.01",
        title="Every UC file listed in UC README table",
        severity="MAJOR",
        score=3 if ok_listed else 0,
        max_score=3,
        what_failed=f"มีไฟล์ UC ที่ไม่อยู่ในตาราง: {missing_rows}" if not ok_listed else "",
        how_to_fix=["เพิ่ม row ในตารางให้ครบทุกไฟล์ UC และให้คอลัมน์ File ตรงชื่อไฟล์เป๊ะ"] if not ok_listed else [],
        evidence={**evidence_path(PATH, True), "uc_files": [p.name for p in ucs], "listed_files": sorted([x for x in listed if x]), "missing_rows": missing_rows},
    ))

    return out