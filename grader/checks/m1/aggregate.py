# grader/checks/m1/aggregate.py
from __future__ import annotations

from typing import Any, List

from grader.core.context import GradingContext
from grader.checks.m1.run_m1 import run_all as run_m1_all


def run(ctx: GradingContext) -> List[Any]:
    """
    Entry point for M1 checks.
    Runner expects: grader.checks.m1.aggregate.run(ctx) -> Iterable[dict]
    """
    return run_m1_all(ctx)