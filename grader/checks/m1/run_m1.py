# grader/checks/m1/run_m1.py
from __future__ import annotations
from pathlib import Path
import json
from grader.core.models import CategoryResult
from grader.checks.m1.instructions_contract import (
    check_instructions_exists, check_instructions_anchors, check_instructions_normalized_hash
)
from grader.checks.m1.manifest import check_manifest_core
from grader.checks.m1.milestone_readme import (
    check_m1_readme_exists, check_m1_readme_overview_present, check_m1_readme_no_student_fill_in, check_m1_readme_placeholders_replaced
)
from grader.checks.m1.student_summary import (
    check_summary_exists, check_summary_problem_scope_filled, check_summary_out_of_scope, check_summary_key_usecases,
    check_summary_qa_tradeoff, check_summary_open_questions
)
from grader.checks.m1.uc_inventory import (
    check_uc_readme_exists, check_uc_table_headers, check_uc_count, check_uc_filename_kebab_case,
    check_uc_table_lists_all_uc_files, check_uc_table_no_placeholders
)
from grader.checks.m1.uc_fully_dressed_sections import (
    check_uc_required_sections, check_uc_minimum_content
)


def run_m1(repo_root: Path) -> dict:
    # Set canonical hash if you want strict; otherwise None disables
    CANONICAL_INSTRUCTIONS_HASH = None  # e.g. "abc123..." after normalization

    categories = []

    cat_contract = CategoryResult(
        category_id="M1.A",
        title="Contract & Manifest",
        checks=[
            check_instructions_exists(repo_root),
            check_instructions_anchors(repo_root),
            check_instructions_normalized_hash(repo_root, CANONICAL_INSTRUCTIONS_HASH),
            check_manifest_core(repo_root),
        ],
    )
    categories.append(cat_contract)

    cat_readme = CategoryResult(
        category_id="M1.B",
        title="Milestone README",
        checks=[
            check_m1_readme_exists(repo_root),
            check_m1_readme_overview_present(repo_root),
            check_m1_readme_no_student_fill_in(repo_root),
            check_m1_readme_placeholders_replaced(repo_root),
        ],
    )
    categories.append(cat_readme)

    cat_summary = CategoryResult(
        category_id="M1.C",
        title="Student Summary",
        checks=[
            check_summary_exists(repo_root),
            check_summary_problem_scope_filled(repo_root),
            check_summary_out_of_scope(repo_root),
            check_summary_key_usecases(repo_root),
            check_summary_qa_tradeoff(repo_root),
            check_summary_open_questions(repo_root),
        ],
    )
    categories.append(cat_summary)

    cat_uc = CategoryResult(
        category_id="M1.D",
        title="Use Case Descriptions",
        checks=[
            check_uc_readme_exists(repo_root),
            check_uc_table_headers(repo_root),
            check_uc_count(repo_root),
            check_uc_filename_kebab_case(repo_root),
            check_uc_table_lists_all_uc_files(repo_root),
            check_uc_table_no_placeholders(repo_root),
            check_uc_required_sections(repo_root),
            check_uc_minimum_content(repo_root),
        ],
    )
    categories.append(cat_uc)

    earned = sum(c.earned for c in categories)
    possible = sum(c.possible for c in categories)
    passed = earned == possible  # or set a threshold if you want

    result = {
        "milestone": "M1",
        "summary": {
            "earned": earned,
            "possible": possible,
            "passed": passed,
        },
        "categories": [c.to_dict() for c in categories],
    }
    return result


def write_m1_result(repo_root: Path, out_relpath: str = "grading/grading_result_M1.json") -> Path:
    out_path = repo_root / out_relpath
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_m1(repo_root)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
