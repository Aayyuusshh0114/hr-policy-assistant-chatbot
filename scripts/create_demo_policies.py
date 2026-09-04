from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_DIRECTORY = Path(__file__).resolve().parents[1] / "output" / "pdf"

POLICIES = [
    {
        "filename": "Demo_Leave_Management_Policy.pdf",
        "code": "DEMO-HR-LMP-001",
        "title": "Leave Management Policy",
        "version": "Version 1.0 | Effective 1 January 2026",
        "purpose": (
            "This fictional policy defines leave entitlements and the request process for "
            "full-time employees of Acme People Labs."
        ),
        "sections": [
            (
                "1. Eligibility",
                [
                    "All confirmed full-time employees are eligible for paid and sick leave.",
                    "Employees serving probation receive leave on a prorated monthly basis.",
                ],
            ),
            (
                "2. Annual Entitlements",
                [
                    "Paid leave: 21 working days per calendar year, accrued at 1.75 days per month.",
                    "Sick leave: 7 working days per calendar year.",
                    "Casual leave: 6 working days per calendar year.",
                ],
            ),
            (
                "3. Request Process",
                [
                    "Planned leave of three or more days must be requested in the HR portal at least 7 calendar days in advance.",
                    "Emergency leave must be communicated to the reporting manager as soon as reasonably possible.",
                    "Leave is approved only after the reporting manager confirms it in the HR portal.",
                ],
            ),
            (
                "4. Carry Forward",
                [
                    "A maximum of 10 unused paid-leave days may be carried into the next calendar year.",
                    "Sick and casual leave cannot be carried forward or encashed.",
                ],
            ),
        ],
    },
    {
        "filename": "Demo_Employee_Referral_Policy.pdf",
        "code": "DEMO-HR-ERP-002",
        "title": "Employee Referral Policy",
        "version": "Version 1.0 | Effective 1 February 2026",
        "purpose": (
            "This fictional policy explains who may refer candidates and when a referral "
            "reward becomes payable at Acme People Labs."
        ),
        "sections": [
            (
                "1. Eligibility",
                [
                    "All permanent employees may submit referrals, including employees on probation.",
                    "Members of Human Resources, Talent Acquisition, and the hiring panel for the vacancy are not eligible for a reward.",
                    "Candidates already present in the recruitment database during the previous 6 months are not valid referrals.",
                ],
            ),
            (
                "2. Submission",
                [
                    "The employee must submit the candidate through the HR referral portal before the candidate applies through another channel.",
                    "A referral remains active for 90 calendar days from the submission date.",
                ],
            ),
            (
                "3. Reward Schedule",
                [
                    "Level 1 roles: INR 10,000.",
                    "Level 2 roles: INR 25,000.",
                    "Level 3 and above roles: INR 50,000.",
                ],
            ),
            (
                "4. Payment Conditions",
                [
                    "The referred employee must complete 90 calendar days of continuous service.",
                    "The referring employee must be actively employed and not serving notice on the payment date.",
                    "Eligible rewards are paid with the next regular payroll after all conditions are met.",
                ],
            ),
        ],
    },
    {
        "filename": "Demo_Payroll_Policy.pdf",
        "code": "DEMO-HR-PAY-003",
        "title": "Payroll and Payslip Policy",
        "version": "Version 1.0 | Effective 1 March 2026",
        "purpose": (
            "This fictional policy describes monthly payroll timing, cutoffs, payslips, and "
            "salary-query handling at Acme People Labs."
        ),
        "sections": [
            (
                "1. Payroll Schedule",
                [
                    "Monthly salary is credited on the last business day of each calendar month.",
                    "If the scheduled date is a bank holiday, salary is credited on the preceding business day.",
                ],
            ),
            (
                "2. Monthly Cutoff",
                [
                    "Attendance, unpaid leave, and variable-pay changes must reach Payroll by the 20th calendar day.",
                    "Changes received after the cutoff are normally adjusted in the following payroll cycle.",
                ],
            ),
            (
                "3. Payslips and Bank Details",
                [
                    "Digital payslips are published in the HR portal within 2 business days after salary credit.",
                    "Employees must verify bank details in the HR portal before the monthly cutoff.",
                ],
            ),
            (
                "4. Payroll Queries",
                [
                    "Employees should raise salary discrepancies through the Payroll Helpdesk category in the HR portal.",
                    "Payroll acknowledges a query within 2 business days and targets resolution within 5 business days.",
                ],
            ),
        ],
    },
    {
        "filename": "Demo_Separation_Policy.pdf",
        "code": "DEMO-HR-SEP-004",
        "title": "Employee Separation Policy",
        "version": "Version 1.0 | Effective 1 April 2026",
        "purpose": (
            "This fictional policy defines the resignation, notice, handover, clearance, and "
            "settlement process at Acme People Labs."
        ),
        "sections": [
            (
                "1. Resignation",
                [
                    "Employees must submit a resignation request through the HR portal and notify their reporting manager.",
                    "The resignation date is recorded when the completed request reaches the HR portal.",
                ],
            ),
            (
                "2. Notice Period",
                [
                    "Employees in Levels 1 and 2 serve 30 calendar days of notice.",
                    "Employees in Level 3 and above serve 60 calendar days of notice.",
                    "Any notice waiver or buyout requires written approval from Human Resources and the business head.",
                ],
            ),
            (
                "3. Handover and Clearance",
                [
                    "The employee must document active work and complete a manager-approved handover.",
                    "Company equipment, identity cards, access devices, and confidential information must be returned before the last working day.",
                ],
            ),
            (
                "4. Final Settlement",
                [
                    "Full and final settlement is targeted within 45 calendar days after the last working day, subject to completed clearance.",
                    "The relieving letter is issued after clearance and settlement calculations are confirmed.",
                ],
            ),
        ],
    },
]


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(20 * mm, 10 * mm, "Fictional portfolio document - not a real company policy")
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_policy(policy: dict[str, object]) -> Path:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIRECTORY / str(policy["filename"])
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PolicyTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=25,
        textColor=colors.HexColor("#173B57"),
        spaceAfter=6,
    )
    centered = ParagraphStyle(
        "Centered",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8.5,
        textColor=colors.HexColor("#64748B"),
        leading=11,
    )
    heading = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#0F766E"),
        spaceBefore=7,
        spaceAfter=3,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9.3,
        leading=12.5,
        textColor=colors.HexColor("#243447"),
        spaceAfter=2,
    )
    bullet = ParagraphStyle(
        "Bullet", parent=body, leftIndent=12, firstLineIndent=-8, bulletIndent=0
    )
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=21 * mm,
        title=str(policy["title"]),
        author="HR Policy Assistant Portfolio Demo",
    )
    story = [
        Table(
            [[Paragraph("ACME PEOPLE LABS", centered), Paragraph(str(policy["code"]), centered)]],
            colWidths=[85 * mm, 85 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E6F6F3")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9BD8CD")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        ),
        Spacer(1, 10),
        Paragraph(str(policy["title"]), title_style),
        Paragraph(str(policy["version"]), centered),
        Spacer(1, 7),
        Paragraph("Portfolio notice", heading),
        Paragraph(
            "This document is entirely fictional and was created only to demonstrate an HR policy retrieval application. It must not be treated as employment advice or an actual policy.",
            body,
        ),
        Paragraph("Purpose", heading),
        Paragraph(str(policy["purpose"]), body),
    ]
    for section_title, points in policy["sections"]:
        block = [Paragraph(section_title, heading)]
        block.extend(Paragraph(f"- {point}", bullet) for point in points)
        story.append(KeepTogether(block))
    story.extend(
        [
            Spacer(1, 8),
            Paragraph("Document control", heading),
            Table(
                [
                    ["Owner", "People Operations"],
                    ["Review cycle", "Annual"],
                    ["Classification", "Public demo - fictional"],
                ],
                colWidths=[42 * mm, 128 * mm],
                style=TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            ),
        ]
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output_path


def main() -> None:
    for policy in POLICIES:
        print(build_policy(policy))


if __name__ == "__main__":
    main()
