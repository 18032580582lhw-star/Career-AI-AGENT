from career_ai.evals.graders import (
    grade_case,
    grade_forbidden_claims,
    grade_missing_keywords,
    grade_prompt_strategy_count,
    grade_role_title,
)
from career_ai.evals.models import CareerEvalCase, EvalCaseInput, ExpectedCareerSignals
from career_ai.models import (
    CareerFitReport,
    JDAnalysis,
    PromptHarnessResult,
    PromptStrategyScore,
    ResumeMatch,
    SkillGap,
)
from career_ai.workflows.models import CareerFitWorkflowResult


def test_grade_role_title_passes_when_expected_title_matches_report() -> None:
    case = _eval_case(role_title="AI Product Analyst")
    result = _workflow_result(role_title="AI Product Analyst")

    check = grade_role_title(case, result)

    assert check.name == "role_title"
    assert check.passed is True
    assert "AI Product Analyst" in check.message


def test_grade_missing_keywords_fails_when_required_keyword_is_not_reported() -> None:
    case = _eval_case(required_missing_keywords=["stakeholder communication"])
    result = _workflow_result(missing_keywords=["dashboard storytelling"])

    check = grade_missing_keywords(case, result)

    assert check.name == "missing_keywords"
    assert check.passed is False
    assert "stakeholder communication" in check.message


def test_grade_forbidden_claims_fails_when_generated_output_adds_claim() -> None:
    case = _eval_case(forbidden_new_claims=["managed a team of 12"])
    result = _workflow_result(cover_letter_draft="I managed a team of 12 analysts.")

    check = grade_forbidden_claims(case, result)

    assert check.name == "forbidden_claims"
    assert check.passed is False
    assert "managed a team of 12" in check.message


def test_grade_prompt_strategy_count_requires_minimum_strategy_count() -> None:
    case = _eval_case(prompt_strategy_count_min=3)
    result = _workflow_result(strategy_names=["baseline", "structured-agent"])

    check = grade_prompt_strategy_count(case, result)

    assert check.name == "prompt_strategy_count"
    assert check.passed is False
    assert "2/3" in check.message


def test_grade_case_aggregates_check_results_and_failure_status() -> None:
    case = _eval_case(
        role_title="AI Product Analyst",
        required_missing_keywords=["stakeholder communication"],
        forbidden_new_claims=["managed a team of 12"],
        prompt_strategy_count_min=3,
    )
    result = _workflow_result(
        role_title="AI Product Analyst",
        missing_keywords=["dashboard storytelling"],
        strategy_names=["baseline", "structured-agent", "fact-preserving-rewriter"],
    )

    case_result = grade_case(case, result)

    assert case_result.case_id == "case-1"
    assert case_result.passed is False
    assert [check.name for check in case_result.checks] == [
        "role_title",
        "missing_keywords",
        "forbidden_claims",
        "prompt_strategy_count",
    ]


def _eval_case(
    *,
    role_title: str = "AI Product Analyst",
    required_missing_keywords: list[str] | None = None,
    forbidden_new_claims: list[str] | None = None,
    prompt_strategy_count_min: int = 3,
) -> CareerEvalCase:
    return CareerEvalCase(
        id="case-1",
        name="Synthetic case",
        input=EvalCaseInput(
            resume_text="Product analyst with Python and SQL.",
            jd_text="Role: AI Product Analyst. Requires stakeholder communication.",
        ),
        expected=ExpectedCareerSignals(
            role_title=role_title,
            required_missing_keywords=required_missing_keywords or [],
            forbidden_new_claims=forbidden_new_claims or [],
            prompt_strategy_count_min=prompt_strategy_count_min,
        ),
    )


def _workflow_result(
    *,
    role_title: str = "AI Product Analyst",
    missing_keywords: list[str] | None = None,
    cover_letter_draft: str = "I am excited to apply.",
    rewritten_resume: str = "Product analyst with Python and SQL.",
    strategy_names: list[str] | None = None,
) -> CareerFitWorkflowResult:
    missing = missing_keywords or []
    names = strategy_names or ["baseline", "structured-agent", "fact-preserving-rewriter"]
    return CareerFitWorkflowResult(
        report=CareerFitReport(
            jd_analysis=JDAnalysis(
                role_title=role_title,
                seniority="Mid-level",
                requirements=[],
                keywords=[],
            ),
            match=ResumeMatch(
                score=80,
                matched_keywords=[],
                missing_keywords=missing,
                summary="Good fit.",
            ),
            skill_gap=SkillGap(
                missing_skills=missing,
                priority_skills=missing[:3],
                notes=[],
            ),
            bullet_suggestions=[],
            cover_letter_draft=cover_letter_draft,
            rewritten_resume=rewritten_resume,
        ),
        prompt_result=PromptHarnessResult(
            strategies=[
                PromptStrategyScore(name=name, score=80, strengths=[], risks=[])
                for name in names
            ],
            best_strategy_name=names[0] if names else "",
        ),
        steps=[
            "analyze_job_description",
            "score_resume_match",
            "compare_prompt_strategies",
        ],
    )
