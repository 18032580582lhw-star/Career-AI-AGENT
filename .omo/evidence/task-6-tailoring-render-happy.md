# Task 6 Evidence - Tailoring Render Happy

## Public prepare/tailor Observation
Command: career-ai-agent prepare --workspace <temp> --resume-file <synthetic> --jd-file <synthetic> --output json, then career-ai-agent tailor --workspace <temp> --run-id <run_id> --output json.

`	ext
{
  "run_id": "run-20260715042735-78697467",
  "source": "api",
  "state": "rejected",
  "proposal_hash": null,
  "validation_hash": null
}

`

Interpretation: the fake-provider API path completed but returned ejected, so it did not produce an accepted render path.

## Accepted Host Proposal Observation
A no-op host proposal was validated successfully:

`	ext
{
  "run_id": "run-20260715042822-a6246397",
  "source": "host",
  "state": "accepted",
  "proposal_hash": "ce14d9e0617ebe2c592b67b0eb3e4e31ac121dc592ec0b2dd1aac531f540ae93",
  "validation_hash": "c62522217ea44a3d8eb4e5463a72fb206294eec2389e23cb407571958ecf1ac1"
}

`

But immediate public CLI render returned a stable not-render-ready error:

`	ext
run is not render-ready; validate and accept a proposal before rendering

`

Interpretation: accepted generic proposals are not render-ready because render requires a structured proposal plus draft.json and candidate-facts.json. This is a real public-flow blocker captured by the debug run.

## Renderer Happy Path From Accepted Fixture
Command: career-ai-agent render --workspace <accepted-fixture-workspace> --run-id run-20260713-001 --format all --disable-latex-engines --output json

`	ext
{
  "run_id": "run-20260713-001",
  "results": [
    {
      "format": "docx",
      "status": "rendered",
      "backend": "docx",
      "code": null,
      "artifacts": [
        {
          "path": "resume.docx",
          "sha256": "df0c98d53ecbaf91d0c2912e43f24e101054142eea0b4c49b2c2414866178a75",
          "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
      ],
      "manifest_path": "docx.render-manifest.json"
    },
    {
      "format": "pdf",
      "status": "rendered",
      "backend": "html-playwright",
      "code": null,
      "artifacts": [
        {
          "path": "resume.html",
          "sha256": "8016f700548c86fee5474b868c94a56591d93b9efa284ce7f7aed7811b967ead",
          "media_type": "text/html; charset=utf-8"
        },
        {
          "path": "resume.pdf",
          "sha256": "f5b9a276dba27abfa9a90cee3cd8f71dce9a97f02738842c2ab67571912dc61e",
          "media_type": "application/pdf"
        }
      ],
      "manifest_path": "html-playwright.render-manifest.json"
    },
    {
      "format": "tex",
      "status": "rendered",
      "backend": "latex-source",
      "code": null,
      "artifacts": [
        {
          "path": "resume.tex",
          "sha256": "f350a7eafe8655e85ecc474bb9f2be88b0c9d33f8ca1404e9180887483cce0ee",
          "media_type": "application/x-tex"
        }
      ],
      "manifest_path": "latex-source.render-manifest.json"
    },
    {
      "format": "latex-pdf",
      "status": "unavailable",
      "backend": null,
      "code": "latex_no_engine",
      "artifacts": [],
      "manifest_path": null
    }
  ]
}

`

Interpretation: renderer services themselves work when the run is persisted with full accepted document material. DOCX, HTML-PDF, and TEX rendered; LaTeX PDF reported latex_no_engine without blocking the other formats.
