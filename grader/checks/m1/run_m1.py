# grader/checks/m1/run_m1.py
from __future__ import annotations

from typing import Any, Dict, List

from grader.core.context import GradingContext

from grader.checks.m1.instruction_contracts import run_all as run_contracts
from grader.checks.m1.manifest import run as run_manifest
from grader.checks.m1.milestone_readme import run_all as run_readme
from grader.checks.m1.student_summary import run_all as run_summary
from grader.checks.m1.uc_inventory import run_all as run_uc_inventory
from grader.checks.m1.uc_fully_dressed import run_all as run_uc_fully


def run_all(ctx: GradingContext) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    items.extend(run_contracts(ctx, strict_hash=False, canonical_hash=""))
    items.append(run_manifest(ctx))
    items.extend(run_readme(ctx))
    items.extend(run_summary(ctx))
    items.extend(run_uc_inventory(ctx))
    items.extend(run_uc_fully(ctx))

    return items