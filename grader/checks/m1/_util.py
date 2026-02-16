from __future__ import annotations
from pathlib import Path
import hashlib
import re

def repo(ctx) -> Path:
    return Path(ctx.repo_path)

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

def normalize_for_hash(text: str) -> str:
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

def parse_first_md_table(md: str):
    lines = [ln.rstrip() for ln in md.splitlines()]
    for i in range(len(lines) - 2):
        if lines[i].strip().startswith("|") and "|" in lines[i].strip()[1:]:
            header = lines[i].strip()
            sep = lines[i + 1].strip()
            if re.match(r"^\|\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$", sep):
                headers = [c.strip() for c in header.strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cols = [c.strip() for c in lines[j].strip("|").split("|")]
                    if len(cols) < len(headers):
                        cols += [""] * (len(headers) - len(cols))
                    if len(cols) > len(headers):
                        cols = cols[: len(headers)]
                    rows.append({headers[k]: cols[k] for k in range(len(headers))})
                    j += 1
                return headers, rows
    return None

def find_heading_blocks(md: str) -> dict[str, str]:
    lines = md.splitlines()
    blocks: dict[str, list[str]] = {}
    cur = None
    for ln in lines:
        m = re.match(r"^##\s+(.*)\s*$", ln)
        if m:
            cur = m.group(1).strip()
            blocks.setdefault(cur, [])
        elif cur is not None:
            blocks[cur].append(ln)
    return {k: "\n".join(v).strip() for k, v in blocks.items()}

def canon_heading(h: str) -> str:
    h = h.strip().lower()
    h = re.sub(r"\s*\(.*?\)\s*$", "", h).strip()
    h = re.sub(r"\s+", " ", h)
    return h

def has_numbered_list(text: str) -> bool:
    return any(re.match(r"^\s*1\.\s+\S", ln) for ln in text.splitlines())

def has_alt_exception_token(text: str) -> bool:
    return any(re.match(r"^\s*(A|E)\d+\.\s+\S", ln) for ln in text.splitlines())
