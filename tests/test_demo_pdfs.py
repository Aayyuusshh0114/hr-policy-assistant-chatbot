from pathlib import Path

from pypdf import PdfReader

EXPECTED_TEXT = {
    "Demo_Leave_Management_Policy.pdf": "21 working days",
    "Demo_Employee_Referral_Policy.pdf": "90 calendar days",
    "Demo_Payroll_Policy.pdf": "last business day",
    "Demo_Separation_Policy.pdf": "60 calendar days",
}


def test_demo_pdfs_are_single_page_and_extractable() -> None:
    pdf_directory = Path(__file__).resolve().parents[1] / "output" / "pdf"
    for filename, expected_phrase in EXPECTED_TEXT.items():
        reader = PdfReader(pdf_directory / filename)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        assert len(reader.pages) == 1
        assert expected_phrase in text
        assert "fictional" in text.lower()
