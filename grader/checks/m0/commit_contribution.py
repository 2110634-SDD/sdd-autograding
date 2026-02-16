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
            "TEAM.md มีอยู่ แต่ไม่พบรายการสมาชิก/อีเมลในรูปแบบที่ระบบอ่านได้",
            "ใส่รายชื่อสมาชิกในรูปแบบ bullet หรือ table และระบุ commit email ต่อคน",
            "TEAM.md (no parsable members)",
        )

    missing_email_lines = [m.raw_line for m in expected if _looks_like_member_line(m.raw_line) and not m.email]
    if missing_email_lines:
        preview = "\n".join(missing_email_lines[:8])
        if len(missing_email_lines) > 8:
            preview += "\n..."
        return (
            0,
            max_score,
            "มีสมาชิกใน TEAM.md ที่ยังไม่ระบุ email จึงตรวจ contribution แบบอัตโนมัติไม่ได้",
            "ใส่ email ที่ “ใช้ commit จริง” ของแต่ละคน (ดูได้จาก `git log --format=%ae`) ให้ครบทุกคน",
            f"บรรทัดที่ต้องแก้ (TEAM.md):\n{preview}",
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
    return (
        score,
        max_score,
        "พบสมาชิกบางคนยังไม่มี commit (ตรวจจาก author email ใน git history)",
        "ให้สมาชิกทำ commit อย่างน้อย 1 ครั้ง แล้วตรวจว่า `git config user.email` ตรงกับ TEAM.md",
        "missing emails: " + ", ".join(missing_emails),
    )


# ✅ Backward import compatibility: __init__.py expects this name
def evaluate_team_contribution(repo_path: Path) -> Tuple[int, int, str]:
    score, max_score, what, how, ev = _evaluate(repo_path)
    # legacy single comment (ยังเก็บไว้)
    comment = what
    if ev:
        comment += f" | บรรทัดที่ต้องแก้: {ev}"
    if how:
        comment += f" | วิธีแก้: {how}"
    return (score, max_score, comment)


def run(ctx: GradingContext) -> Dict[str, object]:
    score, max_score, what, how, ev = _evaluate(ctx.repo_path)

    passed = (max_score <= 0) or (score >= max_score)

    # policy: check นี้เป็น MAJOR (ไม่ทำให้ FAIL ถ้าคุณใช้เกณฑ์ “FAIL เฉพาะ BLOCKER”)
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
        # keep legacy too
        "comment": "" if passed else (what + (f" | วิธีแก้: {how}" if how else "") + (f" | {ev}" if ev else "")),
    }


def check(ctx: GradingContext) -> Tuple[int, int, str]:
    return evaluate_team_contribution(ctx.repo_path)