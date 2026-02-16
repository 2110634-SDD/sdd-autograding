# grader/core/context.py

import json
import os
from pathlib import Path


class GradingContext:
    def __init__(self, repo_path: Path, milestone: str):
        self.repo_path = repo_path
        self.milestone = milestone

    @classmethod
    def from_env(cls):
        # milestone: normalize ให้ deterministic
        milestone = os.environ.get("MILESTONE", "").strip()
        if not milestone:
            milestone = "UNKNOWN"

        # ✅ Always grade the student repo workspace, even if we run inside sdd-autograding/
        base = (
            os.environ.get("STUDENT_REPO_PATH")
            or os.environ.get("REPO_PATH")
            or os.environ.get("GITHUB_WORKSPACE")
        )

        try:
            repo_path = Path(base).resolve() if base else Path(".").resolve()
        except Exception:
            repo_path = Path.cwd()

        return cls(repo_path, milestone)

    def write_result(self, *, milestone, total, max, items):
        """
        Write grading result.
        - Writes legacy: <repo>/grading_result.json (backward-compatible)
        - Writes milestone-specific: <repo>/grading/grading_result_<M>.json
        This method must never raise.
        """
        result = {
            "milestone": milestone,
            "total": total,
            "max": max,
            "items": items,
        }

        legacy_path = self.repo_path / "grading_result.json"
        milestone_dir = self.repo_path / "grading"
        milestone_path = milestone_dir / f"grading_result_{milestone}.json"

        try:
            payload = json.dumps(result, indent=2, ensure_ascii=False)

            # 1) legacy (backward-compatible)
            legacy_path.write_text(payload, encoding="utf-8")

            # 2) milestone-specific
            milestone_dir.mkdir(parents=True, exist_ok=True)
            milestone_path.write_text(payload, encoding="utf-8")

            print(f"[autograder] repo_path={self.repo_path}")
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