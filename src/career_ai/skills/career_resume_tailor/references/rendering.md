# Rendering

Supported render requests:

- generate DOCX/PDF;
- generate Overleaf .tex;
- use the user's own resume.tex;
- compile LaTeX PDF;
- check the LaTeX environment.

Policy:

- Do not patch user source files.
- Do not skip inspect/validate before rendering.
- Do not compile arbitrary .tex files.
- Do not put raw LaTeX commands in proposals.
- Do not run shell compilation directly from the host.
- Do not render unless validation is accepted and current.

For a user-owned `resume.tex`, call `inspect-latex` first. If section mapping is
inferred rather than marker-confirmed, get user confirmation before any patching
or rendering output. Renderer output is written to run-owned artifacts only.
