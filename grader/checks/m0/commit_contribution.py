# grader/checks/m0/commit_contribution.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from grader.core.context import GradingContext

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")


@dataclass(frozen=True)
class ExpectedMember:
    raw_line: str
    email: Optional[str]


def _run_git(repo: Path, args: List[str]) -> str:
    p = subprocess.run(
        ["git"] + args,
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def _is_heading(s: str) -> bool:
    t = s.strip()
    return t.startswith("#")


def _is_hr(s: str) -> bool:
    # Markdown horizontal rule (---, ***)
    t = s.strip()
    return t in ("---", "***") or re.fullmatch(r"[-*_]{3,}", t) is not None


def _is_table_separator_or_header(s: str) -> bool:
    """
    Ignore Markdown table header/separator rows:
      | Student ID | Name | ... |
      |----------- |------| ... |
    """
    t = s.strip()
    if not t.startswith("|"):
        return False
    if "Student ID" in t or "Commit Email" in t or "GitHub Username" in t:
        return True
    # separator row: only pipes, dashes, colons, spaces
    if re.fullmatch(r"[|\-\s:]+", t):
        return True
    return False


def _is_member_table_row(s: str) -> bool:
    """
    Accept only real member table data rows.
    Require:
      - starts with '|'
      - NOT header/separator
      - contains a student id token OR github url (heuristic)
    """
    t = s.strip()
    if not t.startswith("|"):
        return False
    if _is_table_separator_or_header(t):
        return False
    has_student_id = re.search(r"\b\d{8,}\b", t) is not None
    has_github = "github.com/" in t.lower()
    return has_student_id or has_github


def _extract_team_members_section(lines: List[str]) -> List[str]:
    """
    Only parse lines inside the '## Team Members' section.
    This prevents accidental parsing of bullets in Notes/other sections.
    """
    in_section = False
    section_lines: List[str] = []

    for ln in lines:
        s = ln.rstrip("\n")

        # Start when we see heading "## Team Members" (case-insensitive)
        if re.match(r"^\s*##\s+Team\s+Members\s*$", s, flags=re.IGNORECASE):
            in_section = True
            continue

        if not in_section:
            continue

        # Stop on next same-level heading (## ...) other than Team Members
        if re.match(r"^\s*##\s+\S", s) and not re.match(r"^\s*##\s+Team\s+Members\s*$", s, flags=re.IGNORECASE):
            break

        # Also stop at a horizontal rule right after table (common template)
        if _is_hr(s.strip()):
            break

        section_lines.append(s)

    return section_lines


def _parse_expected_members(team_md: Path) -> List[ExpectedMember]:
    if not team_md.exists():
        return []

    raw_lines = team_md.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = _extract_team_members_section(raw_lines)

    out: List[ExpectedMember] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue

        # Only accept member rows from the table in Team Members section
        if not _is_member_table_row(s):
            continue

        emails = EMAIL_RE.findall(s)
        email = emails[0].lower() if emails else None
        out.append(ExpectedMember(raw_line=s, email=email))

    # Deduplicate by email (prefer first occurrence)
    seen: Set[str] = set()
    uniq: List[ExpectedMember] = []
    for m in out:
        key = m.email or m.raw_line
        if key in seen:
            continue
        seen.add(key)
        uniq.append(m)
    return uniq


def _get_contributor_emails(repo: Path) -> Set[str]:
    raw = _run_git(repo, ["log", "--all", "--format=%ae"])
    emails: Set[str] = set()
    for line in raw.splitlines():
        e = line.strip().lower()
        if e and "@" in e:
            emails.add(e)
    return emails


def _evaluate(repo_path: Path) -> Tuple[int, int, str, str, str]:
    """
    Returns: (score, max_score, what_failed, how_to_fix, evidence)
    """
    max_score = 6
    team_md = repo_path / "TEAM.md"

    if not team_md.exists():
        return (
            0,
            max_score,
            "ไม่พบ TEAM.md จึงตรวจ contribution ไม่ได้",
            "สร้าง/เพิ่มไฟล์ TEAM.md ตาม template ที่กำหนด",
            "TEAM.md (missing)",
        )

    expected = _parse_expected_members(team_md)
    if not expected:
        return (
            0,
            max_score,
            "TEAM.md มีอยู่ แต่ไม่พบตารางรายชื่อในหัวข้อ '## Team Members' ในรูปแบบที่ระบบอ่านได้",
            "ตรวจว่า TEAM.md มีหัวข้อ '## Team Members' และมีตารางสมาชิก (| ... | ... | Commit Email |) อยู่ใต้หัวข้อนั้น",
            "TEAM.md: missing or unparsable Team Members table",
        )

    # Member rows without email (should now point to actual member rows only)
    missing_email_rows = [m.raw_line for m in expected if m.email is None]
    if missing_email_rows:
        preview = "\n".join([f"- {ln}" for ln in missing_email_rows[:10]])
        if len(missing_email_rows) > 10:
            preview += "\n- ..."
        return (
            0,
            max_score,
            "มีสมาชิกในตาราง Team Members ที่ยังไม่ระบุ Commit Email จึงตรวจ contribution แบบอัตโนมัติไม่ได้",
            "ใส่ Commit Email ที่ “ใช้ commit จริง” ของแต่ละคน (ดูได้จาก `git log --format=%ae`) ให้ครบทุกคน",
            f"แถวที่ต้องแก้ (TEAM.md / Team Members table):\n{preview}",
        )

    contrib_emails = _get_contributor_emails(repo_path)
    expected_emails = sorted({m.email for m in expected if m.email})

    missing_emails = [e for e in expected_emails if e not in contrib_emails]
    if not missing_emails:
        return (
            max_score,
            max_score,
            "",
            "",
            "ตรวจจาก author email ใน git history: ทุกคนมีอย่างน้อย 1 commit",
        )

    score = max(0, max_score - len(missing_emails) * 3)
    missing_list = "\n".join([f"- {e}" for e in missing_emails])

    return (
        score,
        max_score,
        "พบสมาชิกบางคนยังไม่มี commit (ตรวจจาก author email ใน git history)",
        "ให้สมาชิกทำ commit อย่างน้อย 1 ครั้ง แล้วตรวจว่า `git config user.email` ตรงกับ TEAM.md",
        f"อีเมลที่ยังไม่มี commit:\n{missing_list}",
    )


# Backward import compatibility: __init__.py expects this name
def evaluate_team_contribution(repo_path: Path) -> Tuple[int, int, str]:
    score, max_score, what, how, ev = _evaluate(repo_path)
    comment = what
    if ev:
        comment += f"\n{ev}"
    if how:
        comment += f"\nวิธีแก้: {how}"
    return (score, max_score, comment)


def run(ctx: GradingContext) -> Dict[str, object]:
    score, max_score, what, how, ev = _evaluate(ctx.repo_path)

    passed = (max_score <= 0) or (score >= max_score)
    severity = "MAJOR" if not passed else "INFO"

    return {
        "id": "commit.contribution",
        "title": "Team commit contribution",
        "severity": severity,
        "score": score,
        "max_score": max_score,
        "passed": passed,
        "what_failed": "" if passed else what,
        "how_to_fix": "" if passed else how,
        "evidence": "" if passed else ev,
        # keep legacy too (multi-line)
        "comment": "" if passed else (what + ("\n" + ev if ev else "") + ("\nวิธีแก้: " + how if how else "")),
    }


def check(ctx: GradingContext) -> Tuple[int, int, str]:
    return evaluate_team_contribution(ctx.repo_path)
