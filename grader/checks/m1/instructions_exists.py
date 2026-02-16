from ._util import repo

def run(ctx):
    path = repo(ctx) / "milestone1" / "INSTRUCTIONS.md"
    if path.exists():
        return 2, 2, "OK: milestone1/INSTRUCTIONS.md exists"
    return 0, 2, (
        "[BLOCKER] Missing milestone1/INSTRUCTIONS.md\n"
        "Why: This file is the milestone contract and must not be edited/removed.\n"
        "Fix: Restore it from the assignment template repository."
    )
