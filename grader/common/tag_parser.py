# grader/common/tag_parser.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Literal

TagStyle = Literal["mn-ak", "final", "legacy-v", "legacy-m"]

@dataclass(frozen=True)
class SubmissionTag:
    raw: str
    milestone: str  # "M1", "M2", "M3"
    attempt: str    # "1", "2", ... or "final"
    style: TagStyle

_TAG_MN_AK = re.compile(r"^m(?P<ms>\d+)-a(?P<k>[1-9]\d*)$")
_TAG_M3_FINAL = re.compile(r"^m3-final$")

_TAG_V_ATTEMPT = re.compile(r"^v(?P<ms>\d+)\.(?P<attempt>\d+)-m(?P<mnum>\d+)$")
_TAG_V_RUBRIC  = re.compile(r"^v(?P<ms>\d+)\.(?P<attempt>\d+)-M(?P<mnum>\d+)$")
_TAG_V_FINAL   = re.compile(r"^v(?P<ms>\d+)\.0-final$", re.IGNORECASE)

_TAG_EXACT_M = re.compile(r"^M(?P<ms>[0-9]+)$")


def parse_submission_tag(tag: str) -> SubmissionTag:
    tag = (tag or "").strip()
    if not tag:
        raise ValueError("Empty tag")

    m = _TAG_MN_AK.match(tag)
    if m:
        ms = m.group("ms")
        k = m.group("k")
        return SubmissionTag(raw=tag, milestone=f"M{ms}", attempt=k, style="mn-ak")

    if _TAG_M3_FINAL.match(tag):
        return SubmissionTag(raw=tag, milestone="M3", attempt="final", style="final")

    m = _TAG_V_ATTEMPT.match(tag)
    if m:
        ms = m.group("ms")
        mnum = m.group("mnum")
        if ms != mnum:
            raise ValueError(f"Milestone mismatch in tag '{tag}' (v{ms} but m{mnum})")
        return SubmissionTag(raw=tag, milestone=f"M{ms}", attempt=m.group("attempt"), style="legacy-v")

    m = _TAG_V_RUBRIC.match(tag)
    if m:
        ms = m.group("ms")
        mnum = m.group("mnum")
        if ms != mnum:
            raise ValueError(f"Milestone mismatch in tag '{tag}' (v{ms} but M{mnum})")
        return SubmissionTag(raw=tag, milestone=f"M{ms}", attempt=m.group("attempt"), style="legacy-v")

    m = _TAG_V_FINAL.match(tag)
    if m:
        ms = m.group("ms")
        return SubmissionTag(raw=tag, milestone=f"M{ms}", attempt="final", style="legacy-v")

    m = _TAG_EXACT_M.match(tag)
    if m:
        ms = m.group("ms")
        return SubmissionTag(raw=tag, milestone=f"M{ms}", attempt="1", style="legacy-m")

    raise ValueError(
        "Invalid tag format. Expected one of:\n"
        "  - m<N>-a<K>     (K starts at 1)  e.g., m1-a1, m2-a3\n"
        "  - m3-final      (optional final submission)\n"
        "Legacy accepted during transition:\n"
        "  - v<N>.<K>-m<N>  e.g., v2.1-m2\n"
        "  - v<N>.<K>-M<N>  e.g., v2.0-M2\n"
        "  - v3.0-final\n"
        "  - M1 / M2 / M3"
    )


def try_parse_submission_tag(tag: Optional[str]) -> Optional[SubmissionTag]:
    if not tag:
        return None
    try:
        return parse_submission_tag(tag)
    except ValueError:
        return None