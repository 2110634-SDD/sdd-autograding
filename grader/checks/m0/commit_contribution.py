import re

from grader.utils import (
    read_team_file,
    parse_team_members,
    git_commit_emails,
    git_commit_emails_range,
    git_tag_exists,
)


def _matches_github_noreply(commit_email: str, github_username: str) -> bool:
    """
    Match GitHub noreply formats:
    - user@users.noreply.github.com
    - 12345+user@users.noreply.github.com
    """
    u = re.escape(github_username.strip())
    pattern = rf"^(?:\d+\+)?{u}@users\.noreply\.github\.com$"
    return re.match(pattern, commit_email.strip(), re.IGNORECASE) is not None


def _range_for_milestone(milestone: str) -> str | None:
    """
    Commit range policy:
    - M2: only commits after tag M1 => 'M1..HEAD'
    - M3: only commits after tag M2 => 'M2..HEAD'
    """
    if milestone == "M2":
        return "M1..HEAD"
    if milestone == "M3":
        return "M2..HEAD"
    return None


def _base_tag_for_range(rev_range: str) -> str | None:
    # 'M1..HEAD' -> 'M1'
    if ".." in rev_range:
        return rev_range.split("..", 1)[0]
    return None


def run(ctx):
    max_score = 8
    debug = getattr(ctx, "debug", False)
    milestone = getattr(ctx, "milestone", "")

    try:
        text = read_team_file(ctx)
    except FileNotFoundError:
        return 0, max_score, "ไม่พบไฟล์ TEAM.md"

    members = parse_team_members(text)
    if not members:
        return 0, max_score, (
            "ไม่สามารถตรวจสอบ commit ได้ "
            "(ไม่พบข้อมูลสมาชิกในตาราง Team Members)"
        )

    note = ""
    rev_range = _range_for_milestone(milestone)

    if milestone == "M0":
        # M0: only commits touching TEAM.md
        commit_emails = git_commit_emails(
            ctx.repo_path,
            file_path="TEAM.md",
            debug=debug,
        )
        note = " (ตรวจเฉพาะ commit ที่แตะไฟล์ TEAM.md)"

    elif rev_range is not None:
        # M2/M3: only commits in the range after previous milestone tag
        base_tag = _base_tag_for_range(rev_range)
        if base_tag and not git_tag_exists(ctx.repo_path, base_tag, debug=debug):
            return (
                0,
                max_score,
                (
                    f"ไม่พบ tag '{base_tag}' ใน repository จึงไม่สามารถตรวจ commit หลัง {base_tag} ได้ "
                    f"(ต้องมี tag '{base_tag}' ก่อนสำหรับการตรวจ milestone {milestone})"
                ),
            )

        commit_emails = git_commit_emails_range(ctx.repo_path, rev_range, debug=debug)
        note = f" (ตรวจเฉพาะ commit ช่วง: {rev_range})"

    else:
        # default safe behavior (should not be used if you exclude this check from other milestones)
        commit_emails = git_commit_emails(ctx.repo_path, file_path=None, debug=debug)
        note = " (ตรวจ commit ทั้ง repository)"

    if not commit_emails:
        return 0, max_score, (
            "ไม่พบ commit ใด ๆ ที่ใช้ตรวจสอบได้ "
            "(กรุณาให้สมาชิกแต่ละคน commit อย่างน้อย 1 ครั้งตามเงื่อนไข)"
            + note
        )

    missing = []
    for m in members:
        expected_email = (m.get("email") or "").strip()
        github = (m.get("github") or "").strip()

        ok = False

        # 1) exact email match is the primary criterion
        if expected_email and expected_email in commit_emails:
            ok = True
        else:
            # 2) allow GitHub noreply match if GitHub username is provided
            if github:
                ok = any(_matches_github_noreply(e, github) for e in commit_emails)

        if not ok:
            if expected_email:
                missing.append(expected_email)
            elif github:
                missing.append(f"{github}@users.noreply.github.com")
            else:
                missing.append("<unknown member>")

    if missing:
        penalty_per_member = 2
        penalty = len(missing) * penalty_per_member
        score = max(0, max_score - penalty)
        return (
            score,
            max_score,
            (
                "ไม่พบ commit จากสมาชิกบางคน "
                f"(หัก {penalty_per_member} คะแนนต่อคน): "
                + ", ".join(missing)
                + note
            ),
        )

    return max_score, max_score, "สมาชิกทุกคนมี commit ตามเงื่อนไข" + note