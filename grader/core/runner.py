from grader.core.result import GradingResult
from grader.checks.m0 import team_file

class GradingRunner:
    def __init__(self, ctx):
        self.ctx = ctx

    def run(self):
        result = GradingResult(self.ctx.milestone)

        score, max_score, comment = team_file.run(self.ctx)
        result.add(
            item_id="team_file.exists",
            score=score,
            max_score=max_score,
            comment=comment
        )

        return result