# AI Career Intelligence Suite v0.1 Design

## Scope

Build a local Streamlit MVP that accepts resume text from upload or sample data, accepts a pasted job description, and produces structured career intelligence without adding auth, persistence, payments, deployment, or RAG.

## Architecture

- `app.py`: Streamlit UI only. It gathers input, calls the domain layer, and renders tabs.
- `career_ai.models`: frozen Pydantic response models for JD analysis, matching, missing skills, bullet suggestions, cover letter, and prompt strategy results.
- `career_ai.text_processing`: text extraction, normalization, keyword and skill matching.
- `career_ai.analysis`: pure orchestration functions that produce the MVP outputs.
- `career_ai.prompt_harness`: loads prompt markdown files and scores at least three prompting strategies with deterministic rubric metrics.
- `prompts/`: separate markdown prompt templates.

## Safety Rules

The bullet rewriter must not invent facts. It can only rephrase existing resume bullets and may append JD keywords already present in the original bullet or strongly evidenced by the resume text. Cover letters use only resume/JD-derived details and avoid specific fabricated claims.

## Testing

Unit tests cover JD analysis, match scoring, missing skill detection, bullet rewrite fact preservation, sample fallback, and the three-strategy prompt harness.
