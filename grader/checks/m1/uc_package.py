from ._util import (
    repo, read_text, parse_first_md_table, find_heading_blocks,
    canon_heading, has_numbered_list, has_alt_exception_token
)
from pathlib import Path
import re

UC_NAME_RE = re.compile(r"^UC\d\d-[A-Za-z0-9]+(-[A-Za-z0-9]+)*\.md$")
REQUIRED_HEADERS = {"Use Case ID", "Use Case Name", "Primary Actor", "File"}

REQUIRED_SECTIONS = {
    "primary actor",
    "secondary actors",
    "goal",
    "preconditions",
    "main flow",
    "alternate / exception flows",   # accept Alternative too
    "postconditions",
}

def _uc_files(r: Path):
    base = r / "milestone1" / "use-case-descriptions"
    if not base.exists():
        return []
    files = [p for p in base.glob("UC*.md") if p.is_file()]
    return sorted([p for p in files if re.match(r"^UC\d\d-", p.name)])

def run(ctx):
    r = repo(ctx)
    base = r / "milestone1" / "use-case-descriptions"
    readme = base / "README.md"

    max_score = 20
    issues = []
    score = max_score

    # README exists
    if not readme.exists():
        return 0, max_score, (
            "[BLOCKER] Missing milestone1/use-case-descriptions/README.md\n"
            "Fix: Restore from template and fill the use case inventory table."
        )

    # table headers
    t = parse_first_md_table(read_text(readme))
    if not t:
        issues.append("No markdown table found in UC README")
        score -= 4
        headers, rows = [], []
    else:
        headers, rows = t
        if not REQUIRED_HEADERS.issubset(set(headers)):
            missing = sorted(list(REQUIRED_HEADERS - set(headers)))
            issues.append(f"UC table headers missing: {missing}")
            score -= 4

    # UC files count >=2
    ucs = _uc_files(r)
    if len(ucs) < 2:
        issues.append(f"Found {len(ucs)} UC file(s); need ≥ 2")
        score -= 6

    # filename convention
    bad_names = [p.name for p in ucs if not UC_NAME_RE.fullmatch(p.name)]
    if bad_names:
        issues.append(f"Bad UC filename(s): {bad_names}")
        score -= 3

    # cross-check: each UC file listed in table
    if t:
        listed = set((row.get("File", "") or "").strip() for row in rows)
        missing_rows = [p.name for p in ucs if p.name not in listed]
        if missing_rows:
            issues.append(f"UC files not listed in table: {missing_rows}")
            score -= 3

        # table placeholders
        txt = read_text(readme)
        ph = [tok for tok in ["<ชื่อ use case>", "<actor>", "UC01-<name>.md", "UC02-<name>.md", "UC03-<name>.md"] if tok in txt]
        if ph:
            issues.append(f"UC table still has placeholders: {ph}")
            score -= 2

    # sections + minimum content (cap deductions)
    section_fail = {}
    min_fail = {}

    for p in ucs:
        md = read_text(p)
        blocks = find_heading_blocks(md)
        canon_map = {canon_heading(h): h for h in blocks.keys()}

        # accept "Alternative / Exception Flows"
        if "alternative / exception flows" in canon_map and "alternate / exception flows" not in canon_map:
            canon_map["alternate / exception flows"] = canon_map["alternative / exception flows"]

        missing_sec = [sec for sec in REQUIRED_SECTIONS if sec not in canon_map]
        if missing_sec:
            section_fail[p.name] = missing_sec

        issues_min = []
        pa = canon_map.get("primary actor")
        if not pa or not blocks.get(pa, "").strip():
            issues_min.append("Primary Actor empty")
        mf = canon_map.get("main flow")
        if not mf or not has_numbered_list(blocks.get(mf, "")):
            issues_min.append("Main Flow has no '1.' step")
        af = canon_map.get("alternate / exception flows")
        if not af or not has_alt_exception_token(blocks.get(af, "")):
            issues_min.append("Alt/Exception missing A1./E1.")
        if issues_min:
            min_fail[p.name] = issues_min

    if section_fail:
        issues.append(f"Missing required UC sections: {section_fail}")
        score -= 4  # capped
    if min_fail:
        issues.append(f"UC minimum content issues: {min_fail}")
        score -= 2  # capped

    score = max(0, score)
    if not issues:
        return max_score, max_score, "OK: Use case package (README table + UC files + fully dressed sections) looks good"

    return score, max_score, (
        "[MAJOR] Use case package issues\n"
        + "\n".join([f"- {i}" for i in issues]) + "\n"
        "Why: M1 requires ≥2 fully dressed use cases consistent with the UC inventory table.\n"
        "How to fix:\n"
        "- Ensure UC README has a table with correct headers and no placeholders.\n"
        "- Add at least 2 UC files named UC01-...md, UC02-...md (kebab-case).\n"
        "- In each UC file, include all required sections and minimum flow entries (1., A1./E1.)."
    )
