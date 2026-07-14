from pathlib import Path

import pytest
from pydantic import ValidationError

from career_ai.evals.loader import load_eval_case, load_eval_cases


def test_load_eval_case_preserves_case_id_and_inputs(tmp_path: Path) -> None:
    case_path = tmp_path / "sample.json"
    _ = case_path.write_text(
        """
        {
          "id": "sample-product-analyst",
          "name": "Synthetic AI Product Analyst sample",
          "input": {
            "resume_text": "Product analyst using Python and SQL dashboards.",
            "jd_text": "Role: AI Product Analyst. Requires Python, SQL, Streamlit."
          },
          "expected": {
            "role_title": "AI Product Analyst",
            "required_missing_keywords": ["streamlit"],
            "forbidden_new_claims": ["managed a team of 12"],
            "prompt_strategy_count_min": 3
          }
        }
        """,
        encoding="utf-8",
    )

    case = load_eval_case(case_path)

    assert case.id == "sample-product-analyst"
    assert case.name == "Synthetic AI Product Analyst sample"
    assert case.input.resume_text == "Product analyst using Python and SQL dashboards."
    assert case.input.jd_text == "Role: AI Product Analyst. Requires Python, SQL, Streamlit."
    assert case.expected.role_title == "AI Product Analyst"
    assert case.expected.required_missing_keywords == ["streamlit"]
    assert case.expected.prompt_strategy_count_min == 3


def test_load_eval_case_fails_when_required_fields_are_missing(tmp_path: Path) -> None:
    case_path = tmp_path / "missing-required-fields.json"
    _ = case_path.write_text(
        """
        {
          "id": "broken-case",
          "input": {
            "resume_text": "Resume text only."
          }
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        _ = load_eval_case(case_path)


def test_load_eval_cases_loads_json_files_in_deterministic_order(tmp_path: Path) -> None:
    second_case = tmp_path / "b-case.json"
    first_case = tmp_path / "a-case.json"
    template = """
    {{
      "id": "{case_id}",
      "name": "{name}",
      "input": {{
        "resume_text": "Resume for {name}.",
        "jd_text": "Role: AI Product Analyst. Requires Python."
      }},
      "expected": {{
        "role_title": "AI Product Analyst",
        "required_missing_keywords": [],
        "forbidden_new_claims": [],
        "prompt_strategy_count_min": 3
      }}
    }}
    """
    _ = second_case.write_text(
        template.format(case_id="b-case", name="Second case"),
        encoding="utf-8",
    )
    _ = first_case.write_text(
        template.format(case_id="a-case", name="First case"),
        encoding="utf-8",
    )

    cases = load_eval_cases(tmp_path)

    assert [case.id for case in cases] == ["a-case", "b-case"]


def test_repository_sample_eval_case_loads_resume_and_jd_text() -> None:
    case = load_eval_case(Path("evals/career_cases/sample_product_analyst.json"))

    assert case.id == "sample_product_analyst"
    assert "Product analyst" in case.input.resume_text
    assert "Role: AI Product Analyst" in case.input.jd_text
    assert case.expected.role_title == "AI Product Analyst"


def test_repository_eval_bank_covers_release_quality_roles() -> None:
    # Given: the repository-level deterministic career eval bank.
    cases = load_eval_cases(Path("evals/career_cases"))

    # When: release coverage is inspected.
    case_ids = {case.id for case in cases}

    # Then: eval coverage spans product, business, and career-content workflows.
    assert {
        "sample_product_analyst",
        "business_analyst_gap",
        "career_content_writer_gap",
    } <= case_ids
    assert len(cases) >= 3
    assert all(case.expected.forbidden_new_claims for case in cases)
    assert all(case.expected.prompt_strategy_count_min >= 3 for case in cases)
