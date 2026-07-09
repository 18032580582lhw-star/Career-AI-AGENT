from pathlib import Path

from app import safe_resume_upload_path


def test_safe_resume_upload_path_strips_uploaded_path_segments(tmp_path: Path) -> None:
    path = safe_resume_upload_path(tmp_path, "..\\..\\secret.docx")

    assert path == tmp_path / "secret.docx"
    assert path.resolve().parent == tmp_path.resolve()
