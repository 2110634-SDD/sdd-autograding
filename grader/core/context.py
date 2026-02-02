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

        # repo_path: isolate logic เพื่อ test ได้
        try:
            repo_path = Path(".").resolve()
        except Exception:
            # fallback ที่ deterministic
            repo_path = Path.cwd()

        return cls(repo_path, milestone)

    def write_result(self, *, milestone, total, max, items):
        """
        Write grading result to grading_result.json.
        This method must never raise.
        """
        result = {
            "milestone": milestone,
            "total": total,
            "max": max,
            "items": items,
        }

        out_path = self.repo_path / "grading_result.json"

        try:
            out_path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[autograder] result written to {out_path}")
        except Exception as e:
            # Last line of defense: grading must not crash here
            print("[autograder][FATAL] failed to write grading result")
            print(f"[autograder][FATAL] {e}")
            print("[autograder][FATAL] grading result:")
            try:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception:
                print(str(result))