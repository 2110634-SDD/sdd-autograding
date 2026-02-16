# grader/utils_md.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re


@dataclass
class MdTable:
    headers: List[str]
    rows: List[Dict[str, str]]


def contains_placeholder(text: str, placeholders: List[str]) -> List[str]:
    found = []
    for ph in placeholders:
        if ph in text:
            found.append(ph)
    return found


def find_heading_blocks(md: str) -> Dict[str, str]:
    """
    Extract sections by level-2 headings (## ...).
    Returns mapping of heading_title -> section_body_text (until next ##).
    Case-sensitive keys as-is; caller can canonicalize.
    """
    lines = md.splitlines()
    blocks: Dict[str, List[str]] = {}
    cur = None
    for ln in lines:
        m = re.match(r"^##\s+(.*)\s*$", ln)
        if m:
            cur = m.group(1).strip()
            blocks.setdefault(cur, [])
        elif cur is not None:
            blocks[cur].append(ln)
    return {k: "\n".join(v).strip() for k, v in blocks.items()}


def canonicalize_heading(h: str) -> str:
    h = h.strip().lower()
    # remove parenthetical tails like "(if any)"
    h = re.sub(r"\s*\(.*?\)\s*$", "", h).strip()
    # normalize multiple spaces
    h = re.sub(r"\s+", " ", h)
    return h


def parse_first_md_table(md: str) -> Optional[MdTable]:
    """
    Minimal markdown table parser: find first table of form:
    | a | b |
    |---|---|
    | ..| ..|
    Returns headers + row dicts.
    """
    lines = [ln.rstrip() for ln in md.splitlines()]
    for i in range(len(lines) - 2):
        if lines[i].strip().startswith("|") and "|" in lines[i].strip()[1:]:
            header_line = lines[i].strip()
            sep_line = lines[i + 1].strip()
            if re.match(r"^\|\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$", sep_line):
                headers = [c.strip() for c in header_line.strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cols = [c.strip() for c in lines[j].strip("|").split("|")]
                    # pad/truncate
                    if len(cols) < len(headers):
                        cols += [""] * (len(headers) - len(cols))
                    if len(cols) > len(headers):
                        cols = cols[: len(headers)]
                    rows.append({headers[k]: cols[k] for k in range(len(headers))})
                    j += 1
                return MdTable(headers=headers, rows=rows)
    return None


def has_numbered_list(section_body: str) -> bool:
    # detect "1." at line start
    return any(re.match(r"^\s*1\.\s+\S", ln) for ln in section_body.splitlines())


def has_alt_exception_token(section_body: str) -> bool:
    return any(re.match(r"^\s*(A|E)\d+\.\s+\S", ln) for ln in section_body.splitlines())
