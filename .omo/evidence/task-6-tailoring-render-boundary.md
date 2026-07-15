# Task 6 Evidence - Tailoring Render Boundary

## Stale Template Boundary
After mutating the bound user template, render returned stale:

Command: career-ai-agent render --workspace <accepted-fixture-workspace> --run-id run-20260713-001 --format tex

Exit code: 15

`	ext
Render run: run-20260713-001
Rendered formats: 0/1
- tex: stale (stale)

`

## Unsafe LaTeX Boundary
Command: career-ai-agent inspect-latex --template-file <unsafe-resume.tex> --output json

`	ext
{
  "template_hash": "cf37dad551926e4a9a93d5535b810df8455df7381976f1262d23f30dbb11e5e1",
  "documentclass": "article",
  "preamble_hash": "794d6e100e6b76056bc6815a16ee15916e6ceb5d9044a3caa032aa8787846c21",
  "body_start": 72,
  "body_end": 87,
  "custom_commands": [],
  "sections": [],
  "section_mappings": [],
  "packages": [],
  "fonts": [],
  "unsafe_findings": [
    {
      "code": "latex_shell_escape",
      "command": "write18",
      "line": 1,
      "column": 24,
      "target": null
    },
    {
      "code": "latex_input_outside_root",
      "command": "input",
      "line": 1,
      "column": 38,
      "target": "/etc/passwd"
    }
  ],
  "requires_mapping_confirmation": true
}

`

Interpretation: static inspection caught shell escape and out-of-root input before any LaTeX engine execution.

## Cleanup
- Removed temp root after writing this evidence.
