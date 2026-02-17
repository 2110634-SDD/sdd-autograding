# grader/core/runner.py
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, Iterable, List

from grader.core.context import GradingContext
from grader.core.result import GradingResult, normalize_item


def _canon_milestone(m: str) -> str:
    m = (m or "").strip().upper()
    if not m:
        return "M1"
    if not m.startswith("M"):
        m = f"M{m}"
    return m


@dataclass
class MilestoneAdapter:
    milestone: str
    module_path: str
    entry_func: str = "run"

    def load(self) -> Callable[[GradingContext], Iterable[dict]]:
        """
        Expect module like: grader.checks.m1.aggregate
        with a function: run(ctx) -> Iterable[dict]
        """
        mod = importlib.import_module(self.module_path)
        fn = getattr(mod, self.entry_func, None)
        if fn is None or not callable(fn):
            raise RuntimeError(
                f"Milestone adapter misconfigured: {self.module_path}.{self.entry_func} not found/callable"
            )
        return fn


class Runner:
    """
    Runs checks for a milestone and returns a GradingResult.

    Convention:
      - milestone modules provide run(ctx) -> Iterable[dict] items
      - items are normalized here via normalize_item()
    """

    def __init__(self) -> None:
        self._adapters = {
            "M1": MilestoneAdapter(milestone="M1", module_path="grader.checks.m1.aggregate", entry_func="run"),
            # Future:
            # "M0": MilestoneAdapter(milestone="M0", module_path="grader.checks.m0.aggregate", entry_func="run"),
            # "M2": MilestoneAdapter(...),
        }

    def run(self, milestone: str, ctx: GradingContext) -> GradingResult:
        m = _canon_milestone(milestone)

        adapter = self._adapters.get(m)
        if adapter is None:
            known = ", ".join(sorted(self._adapters.keys()))
            raise RuntimeError(f"Unknown milestone '{m}'. Known milestones: {known}")

        fn = adapter.load()

        raw_items: List[dict] = list(fn(ctx) or [])
        items = [normalize_item(x) for x in raw_items]

        return GradingResult.from_items(items, milestone=m)