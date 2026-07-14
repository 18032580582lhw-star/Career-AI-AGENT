# Workflow

Use explicit file arguments on every host, especially on Windows.

1. Initialize once:
   `career-ai-agent init --workspace <workspace> --agent <codex|claude|opencode|all>`
2. Prepare:
   `career-ai-agent prepare --workspace <workspace> --resume-file <resume> --jd-file <jd> [--latex-template <resume.tex>]`
3. Host proposal:
   write one strict JSON proposal file matching the response schema.
4. Validate:
   `career-ai-agent validate-draft --workspace <workspace> --run-id <run-id> --proposal-file <proposal.json>`
5. Confirm or repair:
   use `career-ai-agent confirm --workspace <workspace> --run-id <run-id> --confirmation-file <confirmation.json>`.
6. Render:
   `career-ai-agent render --workspace <workspace> --run-id <run-id> --format <docx|pdf|tex|latex-pdf|all>`.

Do not use heredoc, shell pipelines, or inline JSON for host handoff. Persist JSON
to a file and pass the file path.
