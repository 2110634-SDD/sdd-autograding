import json

class GradingResult:
    def __init__(self, milestone):
        self.milestone = milestone
        self.items = []
        self.total = 0
        self.max = 0

    def add(self, item_id, score, max_score, comment=""):
        self.items.append({
            "id": item_id,
            "score": score,
            "max": max_score,
            "comment": comment
        })
        self.total += score
        self.max += max_score

    def write_json(self, path):
        with open(path, "w") as f:
            json.dump({
                "milestone": self.milestone,
                "total": self.total,
                "max": self.max,
                "items": self.items
            }, f, indent=2)