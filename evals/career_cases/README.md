# Career Eval Cases

This directory stores synthetic golden cases for deterministic career-agent evals.

Each `*.json` file contains:

- `id`: stable eval case identifier.
- `name`: human-readable case name.
- `input.resume_text`: synthetic resume text.
- `input.jd_text`: synthetic job description text.
- `expected.role_title`: expected extracted role title.
- `expected.required_missing_keywords`: JD keywords that should remain visible as gaps.
- `expected.forbidden_new_claims`: claims that must not appear in rewritten outputs.
- `expected.prompt_strategy_count_min`: minimum number of prompt strategies to compare.

Cases must stay synthetic and non-sensitive. Do not store real resumes, full private job
descriptions, local file paths, contact details, API keys, credentials, cookies, or tokens.
