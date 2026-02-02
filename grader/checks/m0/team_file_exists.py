def run(ctx):
    """
    Check whether TEAM.md exists in repository root.
    """
    team_file = ctx.repo_path / "TEAM.md"

    max_score = 4

    if team_file.exists():
        return max_score, max_score, "พบไฟล์ TEAM.md"
    else:
        return (
            0,
            max_score,
            (
                "ไม่พบไฟล์ TEAM.md ที่ root ของ repository "
                "(กรุณาสร้างไฟล์ TEAM.md ตาม template ที่กำหนดในโจทย์)"
            ),
        )