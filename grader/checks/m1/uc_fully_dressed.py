# grader/checks/m1/uc_fully_dressed.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from ._util import repo, read_text, item

UC_NAME_RE = re.compile(r"^UC\d\d-[A-Za-z0-9]+(-[A-Za-z0-9]+)*\.md$")

REQUIRED_SECTIONS = [
    "Primary Actor",
    "Secondary Actors",
    "Goal",
    "Preconditions",
    "Main Flow",
    "Alternate / Exception Flows",
    "Postconditions",
]


def _uc_files(r: Path) -> List[Path]:
    base = r / "milestone1" / "use-case-descriptions"
    if not base.exists():
        return []
    files = [p for p in base.glob("UC*.md") if p.is_file()]
    out = [p for p in files if re.match(r"^UC\d\d-", p.name)]
    return sorted(out, key=lambda p: p.name)


def _find_headings(md: str) -> Dict[str, str]:
    # map lowercase heading text -> original heading line
    out = {}
    for line in md.splitlines():
        if line.strip().startswith("## "):
            h = line.strip()[3:].strip()
            out[h.lower()] = h
    return out


def _has_numbered_list(block: str) -> bool:
    return bool(re.search(r"^\s*1\.\s+\S+", block, flags=re.MULTILINE))


def _has_alt_exception_token(block: str) -> bool:
    return bool(re.search(r"^\s*(A|E)\d+\.\s+\S+", block, flags=re.MULTILINE))


def _extract_section(md: str, heading: str) -> str:
    # naive: find "## heading" then take until next "## "
    pat = re.compile(rf"^##\s+{re.escape(heading)}\s*$", flags=re.MULTILINE)
    m = pat.search(md)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", md[start:], flags=re.MULTILINE)
    end = start + nxt.start() if nxt else len(md)
    return md[start:end].strip()


def run_all(ctx):
    r = repo(ctx)
    ucs = _uc_files(r)

    # PACK.03 count >=2
    ok_count = len(ucs) >= 2
    item_pack03 = item(
        item_id="M1.UC.PACK.03",
        title="UC files count ≥ 2",
        severity="BLOCKER",
        score=4 if ok_count else 0,
        max_score=4,
        what_failed=f"พบไฟล์ UC {len(ucs)} ไฟล์ (< 2)" if not ok_count else "",
        how_to_fix=["สร้างไฟล์ UC อย่างน้อย 2 ไฟล์ เช่น UC01-xxx.md, UC02-yyy.md"] if not ok_count else [],
        evidence={"uc_count": len(ucs), "uc_files": [p.name for p in ucs]},
    )

    # NAME.01 filename convention
    bad = [p.name for p in ucs if not UC_NAME_RE.fullmatch(p.name)]
    ok_name = (len(bad) == 0)
    item_name01 = item(
        item_id="M1.UC.NAME.01",
        title="UC filenames follow kebab-case convention",
        severity="MAJOR",
        score=3 if ok_name else 0,
        max_score=3,
        what_failed=f"ชื่อไฟล์ UC ไม่ตรง pattern: {bad}" if not ok_name else "",
        how_to_fix=["เปลี่ยนชื่อไฟล์เป็น UC01-foo-bar.md (kebab-case)"] if not ok_name else [],
        evidence={"bad_names": bad, "pattern": UC_NAME_RE.pattern},
    )

    # SECTION.01 required headings per file (capped)
    section_fail: Dict[str, List[str]] = {}
    min_fail: Dict[str, List[str]] = {}

    for p in ucs:
        md = read_text(p)
        headings = _find_headings(md)

        # accept alternative spelling
        if "alternative / exception flows" in headings and "alternate / exception flows" not in headings:
            headings["alternate / exception flows"] = headings["alternative / exception flows"]

        missing = []
        for h in REQUIRED_SECTIONS:
            if h.lower() not in headings:
                missing.append(h)
        if missing:
            section_fail[p.name] = missing

        # minimum signals (optional but useful)
        issues = []
        pa = headings.get("primary actor")
        if not pa or not _extract_section(md, pa).strip():
            issues.append("Primary Actor empty")
        mf = headings.get("main flow")
        if not mf or not _has_numbered_list(_extract_section(md, mf)):
            issues.append("Main Flow has no '1.' step")
        af = headings.get("alternate / exception flows")
        if not af or not _has_alt_exception_token(_extract_section(md, af)):
            issues.append("Alt/Exception missing A1./E1.")
        if issues:
            min_fail[p.name] = issues

    ok_sections = (len(section_fail) == 0)
    item_section01 = item(
        item_id="M1.UC.SECTION.01",
        title="Required UC sections present (per file)",
        severity="BLOCKER",
        score=4 if ok_sections else 0,
        max_score=4,
        what_failed="บางไฟล์ UC ขาดหัวข้อที่จำเป็น" if not ok_sections else "",
        how_to_fix=[
            "ตรวจทุกไฟล์ UC ให้มีหัวข้อครบ: Primary Actor, Secondary Actors, Goal, Preconditions, Main Flow, Alternate/Exception Flows, Postconditions"
        ] if not ok_sections else [],
        evidence={"missing_sections": section_fail},
    )

    # MIN.01 (ให้เป็น MAJOR คะแนน 2/2 หรือ 0/2) — ถ้าคุณอยากปิด ให้เปลี่ยน score/max เป็น 0/0
    ok_min = (len(min_fail) == 0)
    item_min01 = item(
        item_id="M1.UC.MIN.01",
        title="Minimum content signals (per file)",
        severity="MAJOR",
        score=2 if ok_min else 0,
        max_score=2,
        what_failed="บางไฟล์ UC มีเนื้อหาขั้นต่ำไม่ครบ (flow/actor ว่าง)" if not ok_min else "",
        how_to_fix=[
            "Primary Actor ต้องไม่ว่าง",
            "Main Flow ต้องมีอย่างน้อย 1. ...",
            "Alternate/Exception ต้องมี A1. หรือ E1. อย่างน้อย 1 บรรทัด",
        ] if not ok_min else [],
        evidence={"min_content_issues": min_fail},
    )

    return [item_pack03, item_name01, item_section01, item_min01]