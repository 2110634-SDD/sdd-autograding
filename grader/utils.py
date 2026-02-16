import re
import subprocess
import sys
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


def _dbg(msg: str, debug: bool):
    if debug:
        print(f"[debug] {msg}", file=sys.stderr)


def _git(cmd, cwd: Path, debug: bool):
    _dbg(f"git cmd: {' '.join(cmd)} (cwd={cwd})", debug)
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _git_toplevel(repo_path: Path, debug: bool) -> Path | None:
    try:
        r = _git(["git", "rev-parse", "--show-toplevel"], cwd=repo_path, debug=debug)
        top = r.stdout.strip()
        return Path(top).resolve() if top else None
    except Exception as e:
        _dbg(f"git rev-parse failed: {e}", debug)
        return None


def git_commit_emails(repo_path: Path, file_path=None, debug: bool = False):
    """
    Return set of commit author emails.
    - If file_path is provided: only commits touching that file.
    - If file_path is None: whole repo history.
    Never raises. Returns empty set if git is unavailable.

    NOTE: This is intentionally deterministic and minimal:
    - Uses git toplevel to avoid wrong cwd.
    - Provides limited debug info if enabled.
    """
    try:
        top = _git_toplevel(repo_path, debug=debug) or repo_path.resolve()

        cmd = ["git", "log", "--pretty=%ae"]
        if file_path:
            cmd += ["--", str(file_path)]

        result = _git(cmd, cwd=top, debug=debug)

        emails = [
            e.strip()
            for e in result.stdout.splitlines()
            if is_valid_email(e.strip())
        ]

        # minimal debug output
        if debug:
            _dbg(f"git toplevel: {top}", debug)

            try:
                c = _git(["git", "rev-list", "--count", "HEAD"], cwd=top, debug=debug)
                _dbg(f"commit_count={c.stdout.strip()}", debug)
            except Exception as e:
                _dbg(f"commit_count failed: {e}", debug)

            uniq = sorted(set(emails))
            _dbg(f"unique_emails={len(uniq)}", debug)
            _dbg(f"emails_sample={', '.join(uniq[:10])}", debug)

        return set(emails)

    except Exception as e:
        _dbg(f"git_commit_emails failed: {e}", debug)
        return set()


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))