import json
import os
from pathlib import Path


class GradingContext:
    def __init__(self, repo_path: Path, milestone: str, debug: bool = False):
        self.repo_path = repo_path
        self.milestone = milestone
        self.debug = debug

    @classmethod
    def from_env(cls):
        # milestone: normalize ให้ deterministic
        milestone = os.environ.get("MILESTONE", "").strip()
        if not milestone:
            milestone = "UNKNOWN"

        # debug logging toggle (minimal)
        debug = os.environ.get("GRADER_DEBUG", "").strip().lower() in {"1", "true", "yes"}

        # repo_path: MUST point to student repo root even if workflow cd into sdd-autograding
        # Priority:
        # 1) STUDENT_REPO_PATH (explicit override)
        # 2) GITHUB_WORKSPACE (GitHub Actions standard)
        # 3) local fallback: current directory
        student_repo_path = os.environ.get("STUDENT_REPO_PATH", "").strip()
        workspace = os.environ.get("GITHUB_WORKSPACE", "").strip()

        if student_repo_path:
            repo_path = Path(student_repo_path).resolve()
        elif workspace:
            repo_path = Path(workspace).resolve()
        else:
            # local fallback
            try:
                repo_path = Path(".").resolve()
            except Exception:
                repo_path = Path.cwd()

        if debug:
            print(f"[debug] ctx.milestone={milestone}")
            print(f"[debug] ctx.repo_path={repo_path}")

        return cls(repo_path, milestone, debug=debug)

    def write_result(self, *, milestone, total, max, items):
        """
        Write grading result.
        - Always writes legacy: <repo>/grading_result.json
        - Also writes milestone-specific: <repo>/grading/grading_result_<M>.json
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