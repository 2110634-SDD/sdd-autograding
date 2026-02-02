import re
import subprocess
from pathlib import Path


def read_team_file(ctx):
    """
    Read TEAM.md content.
    Raises FileNotFoundError with clear message if missing.
    """
    team_file = ctx.repo_path / "TEAM.md"
    if not team_file.exists():
        raise FileNotFoundError(
            "TEAM.md not found. Please create TEAM.md in the repository root."
        )

    try:
        return team_file.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read TEAM.md: {e}")


def normalize_header(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


HEADER_ALIASES = {
    "studentid": "id",
    "id": "id",
    "name": "name",
    "githubusername": "github",
    "github": "github",
    "commitemail": "email",
    "email": "email",
}


def parse_team_members(text: str):
    """
    Parse TEAM.md markdown table into list of members.
    Each member is a dict with keys like id, name, github, email.
    Returns empty list if no valid table is found.
    """
    lines = text.splitlines()

    table_lines = [
        line.strip()
        for line in lines
        if "|" in line
    ]

    if len(table_lines) < 2:
        return []

    members = []

    for i, line in enumerate(table_lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        normalized = [normalize_header(c) for c in cells]

        # detect header row
        header_map = {
            idx: HEADER_ALIASES[n]
            for idx, n in enumerate(normalized)
            if n in HEADER_ALIASES
        }

        if len(header_map) >= 2:
            # parse rows after header
            for row in table_lines[i + 1:]:
                if re.match(r"^\|?\s*-+\s*\|", row):
                    continue  # separator row

                values = [c.strip() for c in row.strip("|").split("|")]
                member = {}

                for idx, key in header_map.items():
                    if idx < len(values):
                        member[key] = values[idx]

                email = member.get("email", "").strip()
                if is_valid_email(email):
                    member["email"] = email
                    members.append(member)

            break

    return members


def git_commit_emails(repo_path: Path, file_path="TEAM.md"):
    """
    Return set of commit author emails for given file.
    Never raises. Returns empty set if git is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=%ae", "--", file_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return set()

    return {
        e.strip()
        for e in result.stdout.splitlines()
        if is_valid_email(e.strip())
    }


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))