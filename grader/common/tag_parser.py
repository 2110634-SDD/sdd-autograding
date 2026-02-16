# grader/common/tag_parser.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Literal

TagStyle = Literal["attempt", "rubric", "final"]


@dataclass(frozen=True)
class SubmissionTag:
    raw: str
    milestone: str  # "M1", "M2", "M3"
    attempt: str    # "0", "1", ... or "final"
    style: TagStyle


_TAG_ATTEMPT = re.compile(r"^v(?P<ms>\d+)\.(?P<attempt>\d+)-m(?P<mnum>\d+)$")
_TAG_RUBRIC  = re.compile(r"^v(?P<ms>\d+)\.(?P<attempt>\d+)-M(?P<mnum>\d+)$")
_TAG_FINAL   = re.compile(r"^v(?P<ms>\d+)\.0-final$", re.IGNORECASE)


def parse_submission_tag(tag: str) -> SubmissionTag:
    tag = (tag or "").strip()
    if not tag:
        raise ValueError("Empty tag")

    m = _TAG_ATTEMPT.match(tag)
    if m:
        ms = m.group("ms")
        mnum = m.group("mnum")
        if ms != mnum:
            raise ValueError(f"Milestone mismatch in tag '{tag}' (v{ms} but m{mnum})")
        return SubmissionTag(
            raw=tag,
            milestone=f"M{ms}",
            attempt=m.group("attempt"),
            style="attempt",
        )

    m = _TAG_RUBRIC.match(tag)
    if m:
        ms = m.group("ms")
        mnum = m.group("mnum")
        if ms != mnum:
            raise ValueError(f"Milestone mismatch in tag '{tag}' (v{ms} but M{mnum})")
        return SubmissionTag(
            raw=tag,
            milestone=f"M{ms}",
            attempt=m.group("attempt"),
            style="rubric",
        )

    m = _TAG_FINAL.match(tag)
    if m:
        ms = m.group("ms")
        return SubmissionTag(
            raw=tag,
            milestone=f"M{ms}",
            attempt="final",
            style="final",
        )

    raise ValueError(
        "Invalid tag format. Expected one of:\n"
        "  - v<ms>.<attempt>-m<ms>   (e.g., v2.1-m2)\n"
        "  - v<ms>.<attempt>-M<ms>   (e.g., v2.0-M2)\n"
        "  - v3.0-final"
    )


def try_parse_submission_tag(tag: Optional[str]) -> Optional[SubmissionTag]:
    if not tag:
        return None
    try:
        return parse_submission_tag(tag)
    except ValueError:
        return None