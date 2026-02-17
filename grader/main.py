# grader/main.py
from __future__ import annotations

import os
import sys
from typing import Optional

from grader.core.context import GradingContext
from grader.core.runner import Runner
from tools.render_summary import render_to_github_actions


def _read_milestone(argv: list[str]) -> str:
    """
    Priority:
      1) CLI: python -m grader.main M1
      2) ENV: MILESTONE=M1
      3) default: M1
    """
    if len(argv) >= 2 and argv[1].strip():
        return argv[1].strip()
    env = os.getenv("MILESTONE", "").strip()
    return env or "M1"


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv or sys.argv

    # If user passes milestone by CLI, prefer it.
    # Keep env too for Context.from_env() (it prints/debugs).
    milestone = _read_milestone(argv)
    os.environ["MILESTONE"] = milestone

    ctx = GradingContext.from_env()

    runner = Runner()
    result = runner.run(milestone=milestone, ctx=ctx)

    overall_passed = render_to_github_actions(result, milestone=result.milestone)

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())