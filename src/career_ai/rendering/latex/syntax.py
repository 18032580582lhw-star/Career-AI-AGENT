"""Shared lexical operations that never execute or expand LaTeX."""


def mask_latex_comments(source: str) -> str:
    """Replace comment text with spaces while preserving offsets and newlines."""
    masked: list[str] = []
    in_comment = False
    preceding_backslashes = 0
    for character in source:
        if character == "\n":
            masked.append(character)
            in_comment = False
            preceding_backslashes = 0
            continue
        if in_comment:
            masked.append(" ")
            continue
        if character == "%" and preceding_backslashes % 2 == 0:
            masked.append(" ")
            in_comment = True
            preceding_backslashes = 0
            continue
        masked.append(character)
        preceding_backslashes = preceding_backslashes + 1 if character == "\\" else 0
    return "".join(masked)
