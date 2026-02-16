import re

from grader.utils import (
    read_team_file,
    parse_team_members,
    git_commit_emails,
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


def run(ctx):
    max_score = 8
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

    # IMPORTANT: check whole repo history (not only TEAM.md)
    commit_emails = git_commit_emails(
        ctx.repo_path,
        file_path=None,
        debug=getattr(ctx, "debug", False),
    )

    if not commit_emails:
        return 0, max_score, (
            "ไม่พบ commit ใด ๆ ใน repository "
            "(กรุณา commit งานอย่างน้อย 1 ครั้งต่อสมาชิก)"
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
            # report something useful
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
            ),
        )

    return max_score, max_score, "สมาชิกทุกคนมี commit ใน repository"