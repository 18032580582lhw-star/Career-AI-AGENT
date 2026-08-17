from career_ai import (
    analyze_career_fit,
    build_cover_letter_docx,
    build_resume_docx,
    compare_prompt_strategies,
    fetch_job_description_from_url,
    get_sample_inputs,
    improve_resume_bullets,
)


def test_package_root_exports_public_api() -> None:
    assert callable(analyze_career_fit)
    assert callable(build_cover_letter_docx)
    assert callable(build_resume_docx)
    assert callable(compare_prompt_strategies)
    assert callable(fetch_job_description_from_url)
    assert callable(get_sample_inputs)
    assert callable(improve_resume_bullets)
