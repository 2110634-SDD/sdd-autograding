# grader/checks/m1/uc_inventory.py
from __future__ import annotations
from pathlib import Path
from typing import List
import re
from grader.core.models import Severity
from grader.utils_fs import read_text, find_any, regex_fullmatch
from grader.utils_md import parse_first_md_table
from grader.checks.m1.common import ok, fail, msg


UC_FILE_REGEX = r"^UC\d\d-[A-Za-z0-9]+(-[A-Za-z0-9]+)*\.md$"


def list_uc_files(repo: Path) -> List[Path]:
    base = repo / "milestone1" / "use-case-descriptions"
    if not base.exists():
        return []
    files = [p for p in base.glob("UC*.md") if p.is_file()]
    # Only count ones that look like UCnn-...
    return sorted([p for p in files if re.match(r"^UC\d\d-", p.name)])


def check_uc_readme_exists(repo: Path):
    check_id = "M1.UC.PACK.01"
    title = "use-case-descriptions/README.md exists"
    possible = 1
    path = repo / "milestone1" / "use-case-descriptions" / "README.md"
    if path.exists():
        return ok(check_id, title, possible)
    return fail(check_id, title, 0, possible,
                [msg(Severity.BLOCKER, "Missing use-case-descriptions/README.md",
                     "ไฟล์นี้เป็น inventory ของ use cases และใช้ cross-check กับ UC files",
                     ["Restore README.md from template and fill the table."],
                     str(path))])


def check_uc_table_headers(repo: Path):
    check_id = "M1.UC.PACK.02"
    title = "UC inventory table present with required headers"
    possible = 3
    path = repo / "milestone1" / "use-case-descriptions" / "README.md"
    if not path.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "UC README missing", "Cannot validate table headers.", ["Create README.md"], str(path))])

    text = read_text(path)
    table = parse_first_md_table(text)
    required = {"Use Case ID", "Use Case Name", "Primary Actor", "File"}
    if table and required.issubset(set(table.headers)):
        return ok(check_id, title, possible, debug={"headers": table.headers})

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             "Missing or invalid UC inventory table headers",
             "ตารางใน use-case-descriptions/README.md ต้องมีคอลัมน์หลักเพื่อให้ตรวจความสอดคล้องได้",
             ["Ensure the README contains a markdown table.",
              "Headers must include: Use Case ID | Use Case Name | Primary Actor | File"],
             str(path))],
        debug={"found_table": bool(table), "headers": (table.headers if table else [])},
    )


def check_uc_count(repo: Path):
    check_id = "M1.UC.PACK.03"
    title = "UC files count ≥ 2"
    possible = 4
    ucs = list_uc_files(repo)
    if len(ucs) >= 2:
        return ok(check_id, title, possible, debug={"uc_files": [p.name for p in ucs]})

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.BLOCKER,
             f"Found only {len(ucs)} UC file(s); need at least 2",
             "Milestone 1 requires at least 2 main use cases with fully dressed descriptions",
             ["Add at least 2 files under milestone1/use-case-descriptions/ named UC01-...md, UC02-...md",
              "Follow the provided template headings."],
             evidence="; ".join(str(p) for p in ucs) or "No UC files found")],
        debug={"count": len(ucs)},
    )


def check_uc_filename_kebab_case(repo: Path):
    check_id = "M1.UC.NAME.01"
    title = "UC filenames follow kebab-case convention"
    possible = 3
    ucs = list_uc_files(repo)
    bad = [p.name for p in ucs if not regex_fullmatch(UC_FILE_REGEX, p.name)]
    if not bad:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             f"UC filenames not kebab-case or not in required format: {', '.join(bad)}",
             "Naming convention helps consistent linking and autograding across teams",
             ["Rename files to match: UC01-Place-Order.md (kebab-case; no spaces).",
              "Use only letters/numbers and '-' in the use case name part."],
             evidence="; ".join(bad))],
    )


def check_uc_table_lists_all_uc_files(repo: Path):
    check_id = "M1.UC.TABLE.01"
    title = "Every UC file is listed in UC README table"
    possible = 3

    readme = repo / "milestone1" / "use-case-descriptions" / "README.md"
    if not readme.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "UC README missing", "Cannot cross-check UC inventory.", ["Create README.md"], str(readme))])

    table = parse_first_md_table(read_text(readme))
    if not table:
        return fail(check_id, title, 0, possible, [msg(Severity.MAJOR, "No markdown table found", "Need the inventory table for cross-check.", ["Add the inventory table."], str(readme))])

    ucs = list_uc_files(repo)
    uc_names = [p.name for p in ucs]
    file_col = "File"
    listed = set((row.get(file_col, "") or "").strip() for row in table.rows)
    missing_rows = [f for f in uc_names if f not in listed]

    if not missing_rows:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MAJOR,
             f"UC README table is missing rows for: {', '.join(missing_rows)}",
             "Inventory table must match actual submitted UC files (for traceability and grading)",
             ["Add a row for each UC file in the table.",
              "Ensure the 'File' column matches the filename exactly."],
             evidence=str(readme))],
        debug={"missing_rows": missing_rows, "listed_files": sorted(listed)},
    )


def check_uc_table_no_placeholders(repo: Path):
    check_id = "M1.UC.TABLE.02"
    title = "UC README table does not contain placeholders"
    possible = 2
    readme = repo / "milestone1" / "use-case-descriptions" / "README.md"
    if not readme.exists():
        return fail(check_id, title, 0, possible, [msg(Severity.MINOR, "UC README missing", "Cannot validate placeholders.", ["Create README.md"], str(readme))])

    text = read_text(readme)
    bad_tokens = ["<ชื่อ use case>", "<actor>", "UC01-<name>.md", "UC02-<name>.md", "UC03-<name>.md"]
    found = [t for t in bad_tokens if t in text]
    if not found:
        return ok(check_id, title, possible)

    return fail(
        check_id, title, 0, possible,
        [msg(Severity.MINOR,
             f"UC README still contains placeholder tokens: {', '.join(found)}",
             "Placeholders mean the table has not been filled with real use case info",
             ["Replace placeholders with actual use case names and actors.",
              "Ensure the File column matches real UC filenames."],
             evidence=str(readme))],
        debug={"found": found},
    )
