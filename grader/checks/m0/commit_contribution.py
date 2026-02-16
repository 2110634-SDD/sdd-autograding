# grader/checks/m0/commit_contribution.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from grader.core.context import GradingContext


EMAIL_RE = re.compile(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
GHUSER_RE = re.compile(r"@([A-Za-z0-9\-]{1,39})")  # simplified GitHub username regex


@dataclass(frozen=True)
class ExpectedIdentity:
    raw_line: str
    email: Optional[str]
    github: Optional[str]


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


def parse_expected_identities(team_md: Path) -> List[ExpectedIdentity]:
    if not team_md.exists():
        return []

    lines = team_md.read_text(encoding="utf-8", errors="replace").splitlines()
    out: List[ExpectedIdentity] = []
    for ln in lines:
        ln_strip = ln.strip()
        if not ln_strip:
            continue

        emails = EMAIL_RE.findall(ln_strip)
        ghusers = GHUSER_RE.findall(ln_strip)

        email = emails[0].lower() if emails else None
        github = ghusers[0].lower() if ghusers else None

        looks_memberish = (
            ln_strip.startswith(("-", "*")) or "|" in ln_strip or re.match(r"^\d+[\).\s]", ln_strip) is not None
        )

        if (email or github) and (looks_memberish or True):
            out.append(ExpectedIdentity(raw_line=ln_strip, email=email, github=github))

    # Dedup
    seen: Set[Tuple[Optional[str], Optional[str]]] = set()
    uniq: List[ExpectedIdentity] = []
    for x in out:
        key = (x.email, x.github)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(x)
    return uniq


def get_contributor_emails(repo: Path) -> Set[str]:
    raw = _run_git(repo, ["log", "--all", "--format=%ae"])
    emails = set()
    for line in raw.splitlines():
        e = line.strip().lower()
        if e and "@" in e:
            emails.add(e)
    return emails


def evaluate_team_contribution(repo_path: Path) -> Dict:
    """
    Main implementation: returns an item dict to be placed into result.items/checks.
    """
    team_md = repo_path / "TEAM.md"
    expected = parse_expected_identities(team_md)

    max_score = 6

    if not team_md.exists():
        return {
            "id": "M0.CONTRIB.01",
            "title": "Team members have at least one commit",
            "severity": "BLOCKER",
            "score": 0,
            "max_score": max_score,
            "passed": False,
            "what_failed": "ไม่พบไฟล์ TEAM.md จึงไม่สามารถตรวจการมีส่วนร่วมของสมาชิกได้",
            "how_to_fix": "สร้าง TEAM.md ที่ root ของ repo และใส่รายชื่อสมาชิก (แนะนำใส่ email หรือ @github) แล้วส่งใหม่",
            "evidence": {"path": "TEAM.md"},
        }

    contrib_emails = get_contributor_emails(repo_path)

    if not expected:
        return {
            "id": "M0.CONTRIB.01",
            "title": "Team members have at least one commit",
            "severity": "MAJOR",
            "score": 0,
            "max_score": max_score,
            "passed": False,
            "what_failed": "TEAM.md มีอยู่ แต่ไม่พบ email/@github ของสมาชิกในรูปแบบที่ระบบอ่านได้",
            "how_to_fix": "แก้ TEAM.md ให้แต่ละสมาชิกมีอย่างน้อยหนึ่งอย่าง: email (เช่น name@domain) หรือ @github (แนะนำใส่ email เพื่อให้ตรวจ match ได้ชัด)",
            "evidence": {"path": "TEAM.md"},
        }

    missing_emails: List[str] = []
    has_non_email_entries = False

    for ex in expected:
        if ex.email:
            if ex.email not in contrib_emails:
                missing_emails.append(ex.email)
        else:
            # We cannot reliably map @github -> commit without API; encourage email.
            has_non_email_entries = True

    passed = len(missing_emails) == 0

    # scoring: each missing email costs 3 points (cap at 0)
    score = max_score if passed else max(0, max_score - len(missing_emails) * 3)

    if passed:
        what = "ทุกคนมีอย่างน้อย 1 commit (ตรวจจาก author email ใน git history)"
        sev = "MAJOR"
    else:
        what = "พบสมาชิกบางคนยังไม่มี commit (ตรวจจาก author email): " + ", ".join(missing_emails)
        sev = "BLOCKER"

    how_parts: List[str] = []
    if missing_emails:
        how_parts.append("ให้สมาชิกที่ยังไม่มี commit ทำการ commit อย่างน้อย 1 ครั้ง แล้วส่งใหม่ด้วย tag ครั้งถัดไป")
        how_parts.append("ตรวจว่าเครื่องของสมาชิกตั้งค่า git user.email ให้ตรงกับ email ที่ระบุใน TEAM.md (เพื่อให้ระบบ match ได้)")
    if has_non_email_entries:
        how_parts.append("หมายเหตุ: บางบรรทัดใน TEAM.md ไม่มี email (มีแค่ชื่อ/@github) ระบบจึงตรวจแบบ match ไม่ได้ — แนะนำเพิ่ม email เพื่อให้รายงานชัด")

    return {
        "id": "M0.CONTRIB.01",
        "title": "Team members have at least one commit",
        "severity": sev,
        "score": score,
        "max_score": max_score,
        "passed": passed,
        "what_failed": what,
        "how_to_fix": " | ".join(how_parts),
        "evidence": {"path": "TEAM.md"},
    }


# ---- Adapters for different runner styles ----
def check(ctx: GradingContext) -> Dict:
    return evaluate_team_contribution(ctx.repo_path)


def run(ctx: GradingContext) -> Dict:
    return evaluate_team_contribution(ctx.repo_path)