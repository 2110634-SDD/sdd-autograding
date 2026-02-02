from grader.core.context import GradingContext
from grader.checks.m0 import (
    team_file_exists,
    team_file_content,
    commit_contribution,
)

# Mapping per milestone เพื่อรองรับอนาคต
CHECKSETS = {
    "M0": [
        ("team_file.exists", team_file_exists),
        ("team_file.content", team_file_content),
        ("commit.contribution", commit_contribution),
    ],
}


def _safe_run_check(check_id, check, ctx):
    """
    Run a single check safely.
    Never raises.
    Always returns (score, max_score, comment).
    """
    try:
        result = check.run(ctx)
        if not isinstance(result, tuple) or len(result) != 3:
            raise ValueError(
                f"check.run() must return (score, max_score, comment), got {result}"
            )

        score, max_score, comment = result

        if not isinstance(score, (int, float)) or not isinstance(max_score, (int, float)):
            raise ValueError("score and max_score must be numbers")

        if max_score < 0 or score < 0 or score > max_score:
            raise ValueError(
                f"invalid score values: score={score}, max_score={max_score}"
            )

        return score, max_score, str(comment)

    except Exception as e:
        # Grading UX: นิสิตต้องรู้ว่าเป็น error เชิงระบบ
        return (
            0,
            0,
            f"[SYSTEM ERROR] Check '{check_id}' failed to run: {e}",
        )


def main():
    ctx = GradingContext.from_env()

    checks = CHECKSETS.get(ctx.milestone)
    if not checks:
        ctx.write_result(
            milestone=ctx.milestone,
            total=0,
            max=0,
            items=[
                {
                    "id": "milestone.unsupported",
                    "score": 0,
                    "max": 0,
                    "comment": (
                        f"Unsupported milestone '{ctx.milestone}'. "
                        "Please check assignment configuration."
                    ),
                }
            ],
        )
        return

    items = []
    total = 0
    max_total = 0

    for check_id, check in checks:
        score, max_score, comment = _safe_run_check(check_id, check, ctx)

        items.append({
            "id": check_id,
            "score": score,
            "max": max_score,
            "comment": comment,
        })

        total += score
        max_total += max_score

    ctx.write_result(
        milestone=ctx.milestone,
        total=total,
        max=max_total,
        items=items,
    )


if __name__ == "__main__":
    main()