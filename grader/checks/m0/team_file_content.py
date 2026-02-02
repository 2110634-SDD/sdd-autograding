import re
from grader.utils import read_team_file, parse_team_members

THAI_CHAR_PATTERN = re.compile(r"[ก-๙]")


def extract_section(text, title):
    """
    Extract content under section '## <title>'.
    Returns None if section not found.
    """
    pattern = rf"##\s+{re.escape(title)}\n(.*?)(?:\n##|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def run(ctx):
    try:
        text = read_team_file(ctx)
    except FileNotFoundError:
        return 0, 8, "ไม่พบไฟล์ TEAM.md"

    score = 0
    comments = []

    # 1) Team Name (2 คะแนน)
    team_name = extract_section(text, "Team Name")
    if not team_name:
        comments.append("ไม่พบหัวข้อ ## Team Name")
    elif THAI_CHAR_PATTERN.search(team_name):
        comments.append("ชื่อทีมต้องเป็นภาษาอังกฤษเท่านั้น (ห้ามมีภาษาไทย)")
    else:
        score += 2

    # 2) Project Topic (2 คะแนน)
    topic = extract_section(text, "Project Topic")
    if not topic:
        comments.append("ไม่พบหัวข้อ ## Project Topic")
    else:
        score += 2

    # 3) Project Description (อย่างน้อย 2 บรรทัด) (2 คะแนน)
    desc = extract_section(text, "Project Description")
    if not desc:
        comments.append("ไม่พบหัวข้อ ## Project Description")
    else:
        lines = [l for l in desc.splitlines() if l.strip()]
        if len(lines) < 2:
            comments.append(
                "Project Description ต้องมีคำอธิบายอย่างน้อย 2 บรรทัด"
            )
        else:
            score += 2

    # 4) Team Members table (2 คะแนน)
    members = parse_team_members(text)
    if not members:
        comments.append(
            "ไม่พบตาราง Team Members หรือข้อมูลไม่ครบถ้วน"
        )
    else:
        score += 2

    if score == 8:
        return 8, 8, "ข้อมูลใน TEAM.md ครบถ้วนตามที่กำหนด"

    return score, 8, " / ".join(comments)