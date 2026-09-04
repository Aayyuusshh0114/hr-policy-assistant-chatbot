from pathlib import Path


def test_javascript_targets_the_upload_input() -> None:
    project_root = Path(__file__).resolve().parents[1]
    html = (project_root / "frontend/index.html").read_text()
    javascript = (project_root / "frontend/js/app.js").read_text()

    assert 'id="document-upload"' in html
    assert 'querySelector("#document-upload")' in javascript

