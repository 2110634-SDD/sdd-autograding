# grader/utils_fs.py
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Tuple
import re
import hashlib


def read_text(path: Path) -> str:
    # UTF-8 with fallback; keep it robust for student files
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_for_hash(text: str) -> str:
    # robust normalization: newline + trim each line + collapse blank runs
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n")]
    out = []
    blank = False
    for ln in lines:
        if ln == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip() + "\n"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_any(path: Path, patterns: List[str]) -> List[Path]:
    out = []
    for p in patterns:
        out.extend(path.glob(p))
    return sorted(set(out))


def regex_fullmatch(pattern: str, s: str) -> bool:
    return re.fullmatch(pattern, s) is not None


def first_nonempty_line(text: str) -> Optional[str]:
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return None
