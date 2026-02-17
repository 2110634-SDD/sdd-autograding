# grader/core/context.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class GradingContext:
    """
    GradingContext holds:
    - student repo path
    - milestone id (e.g. M0, M1, ...)
    - submission ref/tag (for UX + versioning)
    - parsed tag info (if tag matches supported schemes)
    """

    def __init__(
        self,
        repo_path: Path,
        milestone: str,
        *,
        submission_ref: str = "",
        submission_tag: str = "",
        parsed_tag: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        self.repo_path = repo_path
        self.milestone = milestone
        self.submission_ref = submission_ref
        self.submission_tag = submission_tag
        self.parsed_tag = parsed_tag or {}
        self.debug = bool(debug)

    @staticmethod
    def _normalize_milestone(raw: str) -> str:
        """
        Normalize milestone input to deterministic form:
        - accept "m1" -> "M1"
        - accept "M1" -> "M1"
        - otherwise return trimmed uppercase
        """
        s = (raw or "").strip()
        if not s:
            return "UNKNOWN"
        s2 = s.upper()
        # common forms: M0..M9
        if len(s2) >= 2 and s2[0] == "M" and s2[1:].isdigit():
            return s2
        return s2

    @staticmethod
    def _env_truthy(name: str, default: str = "0") -> bool:
        v = (os.environ.get(name, default) or "").strip().lower()
        return v in ("1", "true", "yes", "y", "on")

    @classmethod
    def from_env(cls):
        # milestone: normalize deterministic
        milestone = cls._normalize_milestone(os.environ.get("MILESTONE", ""))

        # Always grade the student repo workspace, even if we run inside sdd-autograding/
        base = (
            os.environ.get("STUDENT_REPO_PATH")
            or os.environ.get("REPO_PATH")
            or os.environ.get("GITHUB_WORKSPACE")
        )

        try:
            repo_path = Path(base).resolve() if base else Path(".").resolve()
        except Exception:
            repo_path = Path.cwd()

        submission_ref = (os.environ.get("SUBMISSION_REF") or "").strip()
        submission_tag = (os.environ.get("SUBMISSION_TAG") or "").strip()

        debug = cls._env_truthy("GRADER_DEBUG", default="0")

        parsed_tag: Optional[Dict[str, Any]] = None
        if submission_tag:
            # Parse tag schemes (new: mN-aK, legacy: vN.K-mN, etc.)
            try:
                from grader.common.tag_parser import try_parse_submission_tag  # type: ignore

                t = try_parse_submission_tag(submission_tag)
                if t is not None:
                    parsed_tag = {
                        "raw": t.raw,
                        "milestone": t.milestone,
                        "attempt": t.attempt,
                        "style": t.style,
                    }
            except Exception:
                # Parsing must never break grading
                parsed_tag = None

        ctx = cls(
            repo_path,
            milestone,
            submission_ref=submission_ref,
            submission_tag=submission_tag,
            parsed_tag=parsed_tag,
            debug=debug,
        )

        # Helpful debug prints (safe)
        print(f"[autograder] repo_path={ctx.repo_path}")
        print(f"[autograder] milestone={ctx.milestone}")
        print(f"[autograder] debug={ctx.debug}")
        if ctx.submission_ref:
            print(f"[autograder] submission_ref={ctx.submission_ref}")
        if ctx.submission_tag:
            print(f"[autograder] submission_tag={ctx.submission_tag}")
        if ctx.parsed_tag:
            print(f"[autograder] parsed_tag={ctx.parsed_tag}")

        return ctx

    def write_result(self, *, milestone, total, max, items):
        """
        Write grading result to student repo workspace ONLY when GRADER_DEBUG=1.

        - If not debug: do nothing (must never raise).
        - If debug:
            legacy: <repo>/grading_result.json (backward-compatible)
            milestone-specific: <repo>/grading/grading_result_<M>.json
        """
        if not self.debug:
            print("[autograder] debug disabled; skip writing grading_result*.json")
            return

        milestone_norm = self._normalize_milestone(milestone)

        result: Dict[str, Any] = {
            # core identifiers
            "milestone": milestone_norm,

            # backward-compatible score keys
            "total": total,
            "max": max,
            "items": items,

            # renderer-friendly aliases
            "total_score": total,
            "max_score": max,
            "checks": items,

            # submission metadata (for UI)
            "submission": {
                "ref": self.submission_ref,
                "tag": self.submission_tag,
                "parsed_tag": self.parsed_tag or None,
            },
        }

        legacy_path = self.repo_path / "grading_result.json"
        milestone_dir = self.repo_path / "grading"
        milestone_path = milestone_dir / f"grading_result_{milestone_norm}.json"

        try:
            payload = json.dumps(result, indent=2, ensure_ascii=False)

            # 1) legacy
            legacy_path.write_text(payload, encoding="utf-8")

            # 2) milestone-specific
            milestone_dir.mkdir(parents=True, exist_ok=True)
            milestone_path.write_text(payload, encoding="utf-8")

            print(f"[autograder] result written to {legacy_path}")
            print(f"[autograder] result written to {milestone_path}")

        except Exception as e:
            # Last line of defense: grading must not crash here
            print("[autograder][FATAL] failed to write grading result")
            print(f"[autograder][FATAL] {e}")
            print("[autograder][FATAL] grading result:")
            try:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception:
                print(str(result))