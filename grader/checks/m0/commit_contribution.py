from grader.utils import (
    read_team_file,
    parse_team_members,
    git_commit_emails,
)


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

    commit_emails = git_commit_emails(ctx.repo_path)

    if not commit_emails:
        return 0, max_score, (
            "ไม่พบ commit ใด ๆ ใน repository "
            "(กรุณา commit งานอย่างน้อย 1 ครั้งต่อสมาชิก)"
        )

    member_emails = [
        m.get("email")
        for m in members
        if m.get("email")
    ]

    missing = [
        email
        for email in member_emails
        if email not in commit_emails
    ]

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