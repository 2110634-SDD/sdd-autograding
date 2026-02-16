# grader/checks/m0/commit_contribution.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

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


def _looks_like_member_line(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    return s.startswith(("-", "*")) or "|" in s or re.match(r"^\d+[\).\s]", s) is not None


def _parse_expected_members(team_md: Path) -> List[ExpectedMember]:
    if not team_md.exists():
        return []
    lines = team_md.read_text(encoding="utf-8", errors="replace").splitlines()
    out: List[ExpectedMember] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if not _looks_like_member_line(s) and "@" not in s:
            continue

        emails = EMAIL_RE.findall(s)
        email = emails[0].lower() if emails else None
        out.append(ExpectedMember(raw_line=s, email=email))

    # dedup
    seen = set()
    uniq: List[ExpectedMember] = []
    for m in out:
        key = (m.email, m.raw_line)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(m)
    return uniq


def _get_contributor_emails(repo: Path) -> Set[str]:
    raw = _run_git(repo, ["log", "--all", "--format=%ae"])
    emails = set()
    for line in raw.splitlines():
        e = line.strip().lower()
        if e and "@" in e:
            emails.add(e)
    return emails


def _evaluate(repo_path: Path) -> Tuple[int, int, str]:
    """
    Returns: (score, max_score, comment)
    Compatible with current runner contract.
    """
    max_score = 6
    team_md = repo_path / "TEAM.md"

    if not team_md.exists():
        return (0, max_score, "ไม่พบ TEAM.md จึงตรวจ contribution ไม่ได้")

    expected = _parse_expected_members(team_md)
    if not expected:
        return (0, max_score, "TEAM.md มีอยู่ แต่ไม่พบรายการสมาชิก/อีเมลในรูปแบบที่ระบบอ่านได้")

    # Enforce email presence to make verification deterministic (no API needed)
    missing_email_lines = [m.raw_line for m in expected if _looks_like_member_line(m.raw_line) and not m.email]
    if missing_email_lines:
        preview = " || ".join(missing_email_lines[:5])
        if len(missing_email_lines) > 5:
            preview += " ..."
        return (
            0,
            max_score,
            "มีสมาชิกใน TEAM.md ที่ยังไม่ระบุ email จึงตรวจ contribution แบบอัตโนมัติไม่ได้ | "
            f"บรรทัดที่ต้องแก้: {preview} | "
            "แนะนำ: ใส่ email ที่ใช้ commit จริง (ดูได้จาก git log)",
        )

    contrib_emails = _get_contributor_emails(repo_path)
    expected_emails = sorted({m.email for m in expected if m.email})

    missing_emails = [e for e in expected_emails if e not in contrib_emails]
    if not missing_emails:
        return (max_score, max_score, "ทุกคนมีอย่างน้อย 1 commit (ตรวจจาก author email ใน git history)")

    score = max(0, max_score - len(missing_emails) * 3)
    return (
        score,
        max_score,
        "พบสมาชิกบางคนยังไม่มี commit (ตรวจจาก author email): "
        + ", ".join(missing_emails)
        + " | วิธีแก้: ให้สมาชิกทำ commit อย่างน้อย 1 ครั้ง และตรวจว่า git user.email ตรงกับ TEAM.md",
    )


# ✅ Backward import compatibility: __init__.py expects this name
def evaluate_team_contribution(repo_path: Path) -> Tuple[int, int, str]:
    return _evaluate(repo_path)


# Runner adapters
def run(ctx: GradingContext) -> Tuple[int, int, str]:
    return _evaluate(ctx.repo_path)


def check(ctx: GradingContext) -> Tuple[int, int, str]:
    return _evaluate(ctx.repo_path)