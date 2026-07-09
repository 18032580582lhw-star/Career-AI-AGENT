from career_ai.analysis import analyze_career_fit, get_sample_inputs, improve_resume_bullets


def test_analyze_career_fit_returns_structured_outputs_when_given_sample_inputs() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)

    assert result.jd_analysis.role_title == "AI Product Analyst"
    assert result.match.score >= 60
    assert "python" in result.match.matched_keywords
    assert len(result.bullet_suggestions) >= 2
    assert result.cover_letter_draft.startswith("Dear Hiring Team,")


def test_analyze_career_fit_identifies_missing_skills_when_resume_lacks_jd_terms() -> None:
    resume_text = "Operations coordinator with Excel reporting and stakeholder updates."
    jd_text = "Hiring a data analyst skilled in Python, SQL, Streamlit, and LLM evaluation."

    result = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)

    assert "python" in result.skill_gap.missing_skills
    assert "sql" in result.skill_gap.missing_skills
    assert "streamlit" in result.skill_gap.missing_skills


def test_improve_resume_bullets_preserves_original_facts() -> None:
    bullets = [
        "Built a Streamlit dashboard for weekly hiring funnel reporting.",
        "Analyzed interview conversion trends using Python and SQL.",
    ]
    jd_keywords = ["llm", "python", "stakeholder", "streamlit"]

    suggestions = improve_resume_bullets(
        bullets=bullets,
        jd_keywords=jd_keywords,
        full_resume_text="\n".join(bullets),
    )

    assert suggestions[0].original == bullets[0]
    assert "LLM" not in suggestions[0].improved
    assert suggestions[1].factual_consistency_note == "Preserves original resume facts."


def test_improve_resume_bullets_does_not_borrow_keywords_from_other_bullets() -> None:
    bullets = [
        "Built a Streamlit dashboard for weekly hiring funnel reporting.",
        "Analyzed interview conversion trends using Python and SQL.",
    ]

    suggestions = improve_resume_bullets(
        bullets=bullets,
        jd_keywords=["python", "streamlit"],
        full_resume_text="\n".join(bullets),
    )

    assert "python" not in suggestions[0].improved.lower()
    assert suggestions[0].jd_keywords_used == ["streamlit"]
