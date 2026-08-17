from career_ai.workflows.factual_boundary import (
    BoundaryViolationCode,
    check_career_fit_report,
    guard_career_fit_report,
)

from career_ai.analysis import analyze_career_fit, get_sample_inputs


def test_accepts_valid_career_fit_report_when_output_is_grounded() -> None:
    # Given: deterministic, grounded sample inputs and output.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)

    # When: the workflow boundary checks the serialized report.
    result = check_career_fit_report(
        raw_output=report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: the report crosses the boundary unchanged.
    assert result.accepted
    assert result.report == report
    assert result.violations == []


def test_rejects_invalid_json_before_output_enters_workflow() -> None:
    # Given: malformed JSON and valid source inputs.
    resume_text, jd_text = get_sample_inputs()

    # When: the workflow boundary checks the malformed output.
    result = check_career_fit_report(
        raw_output="{not-json",
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: parsing is rejected with a stable violation code.
    assert not result.accepted
    assert result.report is None
    assert result.violations[0].code == BoundaryViolationCode.INVALID_JSON


def test_rejects_match_score_outside_resume_match_range() -> None:
    # Given: a report whose nested match score exceeds the allowed range.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    unsafe_report = report.model_copy(
        update={"match": report.match.model_copy(update={"score": 101})},
    )

    # When: the workflow boundary checks the report.
    result = check_career_fit_report(
        raw_output=unsafe_report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: the unsafe score is rejected.
    assert [violation.code for violation in result.violations] == [
        BoundaryViolationCode.SCORE_OUT_OF_RANGE,
    ]


def test_rejects_bullet_suggestion_without_source_resume_anchor() -> None:
    # Given: a suggestion whose original bullet is absent from the resume.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    unsafe_suggestion = report.bullet_suggestions[0].model_copy(
        update={"original": "Led a machine learning hiring analytics project."},
    )
    unsafe_report = report.model_copy(update={"bullet_suggestions": [unsafe_suggestion]})

    # When: the workflow boundary checks the report.
    result = check_career_fit_report(
        raw_output=unsafe_report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: the missing resume anchor is rejected.
    assert [violation.code for violation in result.violations] == [
        BoundaryViolationCode.ORIGINAL_NOT_IN_RESUME,
    ]


def test_rejects_jd_keywords_that_do_not_come_from_job_description() -> None:
    # Given: a suggestion containing a keyword absent from the JD.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    unsafe_suggestion = report.bullet_suggestions[0].model_copy(
        update={"jd_keywords_used": ["kubernetes"]},
    )
    unsafe_report = report.model_copy(update={"bullet_suggestions": [unsafe_suggestion]})

    # When: the workflow boundary checks the report.
    result = check_career_fit_report(
        raw_output=unsafe_report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: the unsupported JD keyword is rejected.
    assert [violation.code for violation in result.violations] == [
        BoundaryViolationCode.KEYWORD_NOT_IN_JD,
    ]


def test_rejects_rewritten_resume_with_unsupported_facts() -> None:
    # Given: a rewritten resume containing new company, date, and metric facts.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    unsafe_report = report.model_copy(
        update={
            "rewritten_resume": (
                f"{report.rewritten_resume}\n"
                "- Led Kubernetes migration at Stripe in 2025 with 40% cost savings."
            ),
        },
    )

    # When: the workflow boundary checks the report.
    result = check_career_fit_report(
        raw_output=unsafe_report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then: the invented facts are rejected.
    assert [violation.code for violation in result.violations] == [
        BoundaryViolationCode.UNSUPPORTED_FACT,
    ]


def test_guard_returns_fallback_report_when_output_is_rejected() -> None:
    # Given: malformed output and a deterministic fallback report.
    resume_text, jd_text = get_sample_inputs()
    fallback_report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)

    # When: the guard evaluates the malformed output.
    result = guard_career_fit_report(
        raw_output="{not-json",
        resume_text=resume_text,
        jd_text=jd_text,
        fallback_report=fallback_report,
    )

    # Then: the fallback is used without weakening the violation.
    assert result.report == fallback_report
    assert result.used_fallback
    assert [violation.code for violation in result.violations] == [
        BoundaryViolationCode.INVALID_JSON,
    ]
