from ._util import repo

CORE = [
    "milestone1/README.md",
    "milestone1/STUDENT_SUMMARY.md",
    "milestone1/concrete-quality-attribute-scenarios.md",
    "milestone1/use-case-descriptions/README.md",
    "milestone1/diagrams/README.md",
]

def run(ctx):
    r = repo(ctx)
    missing = [p for p in CORE if not (r / p).exists()]
    if not missing:
        return 8, 8, "OK: milestone1 core files exist"

    score = max(0, 8 - 2 * len(missing))
    return score, 8, (
        "[BLOCKER] Missing milestone1 core files\n"
        f"Missing: {', '.join(missing)}\n"
        "Why: These files are required by the milestone contract.\n"
        "Fix: Create the missing files at the exact paths and commit."
    )
