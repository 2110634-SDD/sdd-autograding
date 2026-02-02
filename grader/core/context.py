import os
from pathlib import Path

class GradingContext:
    def __init__(self, repo_path, milestone):
        self.repo_path = Path(repo_path)
        self.milestone = milestone

    @classmethod
    def from_env(cls):
        milestone = os.environ.get("MILESTONE")
        if not milestone:
            raise RuntimeError("MILESTONE env var not set")

        return cls(
            repo_path=".",
            milestone=milestone
        )