from ._util import repo, read_text

PLACEHOLDERS = [
    "[Student Fill In]",
    "(อธิบายปัญหาโดยสรุป 2–3 บรรทัด)",
]

def run(ctx):
    path = repo(ctx) / "milestone1" / "README.md"
    if not path.exists():
        return 0, 8, "[BLOCKER] Missing milestone1/README.md"

    text = read_text(path)

    issues = []
    if "## Overview" not in text:
        issues.append("Missing section '## Overview'")
    if "[Student Fill In]" in text:
        issues.append("Still contains '[Student Fill In]'")
    for ph in PLACEHOLDERS[1:]:
        if ph in text:
            issues.append(f"Still contains placeholder: {ph}")

    if not issues:
        return 8, 8, "OK: milestone1/README.md filled (no template markers)"

    # scoring: each issue costs 2 points (cap)
    score = max(0, 8 - 2 * len(issues))
    return score, 8, (
        "[MAJOR] milestone1/README.md not filled properly\n"
        f"Issues: {', '.join(issues)}\n"
        "Why: README guides readers where to find artefacts; Overview must be filled.\n"
        "Fix:\n"
        "- Fill the Overview section with 2–3 lines (problem, primary users, main goal).\n"
        "- Remove '[Student Fill In]' and placeholders."
    )
