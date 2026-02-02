from pathlib import Path

def run(ctx):
    team_file = ctx.repo_path / "TEAM.md"
    if team_file.exists():
        return 4, 4, "พบไฟล์ TEAM.md"
    else:
        return 0, 4, "ไม่พบไฟล์ TEAM.md"