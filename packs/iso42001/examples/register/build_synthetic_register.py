"""Build the synthetic AIMS risk register fixture (Acme Feedback Ltd, fictional).

Same eight tabs as the source workbook, plus the UofA onboarding columns and a
Register Checks tab that computes the one-page verification summary in-sheet.
Seeded defects are listed on the last tab so the file works as a test fixture.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = str(Path(__file__).with_name("acme-register.xlsx"))
FONT = "Arial"
HDR_FILL = PatternFill("solid", fgColor="4F81BD")
HDR_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
BODY = Font(name=FONT, size=10)
INPUT_FILL = PatternFill("solid", fgColor="FFFFCC")  # cells the client fills
UOFA_FILL = PatternFill("solid", fgColor="E2EFDA")   # columns UofA adds
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
TODAY = dt.date(2026, 11, 1)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = BORDER


def body(ws, r1, r2, ncols):
    for r in range(r1, r2 + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = BODY
            cell.alignment = WRAP
            cell.border = BORDER


wb = Workbook()

# ---------------------------------------------------------------- 1 Document Control
ws = wb.active
ws.title = "Document Control"
rows = [
    ("Document name", "Acme Feedback Ltd. AI Management System (AIMS) Risk Assessment"),
    ("Document owner", "Head of Security Governance"),
    ("Type", "Risk Assessment"),
    ("Approved by", "Security Governance Committee"),
    ("Issued by", "Security Governance Committee"),
    ("Prepared by", "AI Governance Lead; Risk Analyst"),
    ("Effective date", dt.date(2025, 6, 15)),
    ("Last reviewed date", dt.date(2025, 6, 15)),
    ("Next review date", dt.date(2026, 6, 15)),
]
for i, (k, v) in enumerate(rows, start=1):
    ws.cell(row=i, column=1, value=k).font = Font(name=FONT, bold=True, size=10)
    c = ws.cell(row=i, column=2, value=v)
    c.font = BODY
    c.fill = INPUT_FILL
    if isinstance(v, dt.date):
        c.number_format = "yyyy-mm-dd"
ws["B9"].comment = Comment("Seeded defect D6: next review date is in the past "
                           "relative to the assessment date on Register Checks.", "fixture")
ws.cell(row=11, column=1, value="Version control").font = Font(name=FONT, bold=True, size=10)
for j, h in enumerate(["Date", "Name", "Version", "Description of changes"], start=1):
    ws.cell(row=12, column=j, value=h)
style_header(ws, 12, 4)
ws.cell(row=13, column=1, value=dt.date(2025, 6, 15)).number_format = "yyyy-mm-dd"
ws.cell(row=13, column=2, value="2025 AI Risk Assessment")
ws.cell(row=13, column=3, value="1.0")
ws.cell(row=13, column=4, value="Creation of the document")
body(ws, 13, 13, 4)
ws.cell(row=15, column=1, value="Legend").font = Font(name=FONT, bold=True, size=10)
ws.cell(row=16, column=1, value="Yellow cells").fill = INPUT_FILL
ws.cell(row=16, column=2, value="Client fills these. Everything the source workbook asked for.")
ws.cell(row=17, column=1, value="Green cells").fill = UOFA_FILL
ws.cell(row=17, column=2, value="UofA onboarding columns. Populated by `uofa extract` from the evidence bundle, "
                                "confirmed by the reviewer. Each carries a source comment.")
ws.cell(row=18, column=1, value="White cells")
ws.cell(row=18, column=2, value="Formulas. Do not type over them.")
ws.cell(row=19, column=1, value="Fixture note")
ws.cell(row=19, column=2, value="Acme Feedback Ltd. is fictional. People, systems, dates and controls are invented. "
                                "Structure follows the schema in aims_risk_register_schema.md.")
for r in range(16, 20):
    ws.cell(row=r, column=2).font = BODY
    ws.cell(row=r, column=1).font = BODY
ws.column_dimensions["A"].width = 22
ws.column_dimensions["B"].width = 70
ws.column_dimensions["C"].width = 10
ws.column_dimensions["D"].width = 40

# ---------------------------------------------------------------- 2 Introduction
ws = wb.create_sheet("Introduction")
intro = [
    ("Purpose", "To perform a risk assessment of the AI systems and supporting infrastructure in scope of the AIMS, "
                "as defined in the AIMS Scope and Boundaries document."),
    ("Scope", "All scope items in the AIMS Scope and Boundaries document. Asset classes assessed: "
              "1. Information assets (customer data, company data, user and organization records). "
              "2. Digital assets (system software, models, applications). "
              "3. Physical assets (servers, storage). "
              "4. Site assets (service regions, data centers). "
              "5. People assets (operations, science, QA)."),
    ("Approach", "For each asset class, identify threats and vulnerabilities, rate impact and probability, and derive "
                 "an inherent risk level. For every High and Medium inherent risk a treatment plan is required to reach "
                 "the residual risk. Unmitigated risks need a documented remediation plan and acceptance by the business."),
    ("How to use this workbook", "Tabs are executed left to right. Document Control and Introduction are owned by the "
                                 "document owner. Impact, Probability, Time Horizon, Control Evaluation and Risk Levels "
                                 "are fixed scales. AI Risk Assessment is the master register, populated with each SME, "
                                 "asset owner and risk owner. Register Checks is computed and is not edited."),
    ("UofA extension", "The green columns on AI Risk Assessment are not in the original workbook shape. They hold the "
                       "evidence references and classification flags that turn a self-assessment into a checkable record. "
                       "`uofa extract <bundle>` fills them; `uofa import` carries them into the signed package."),
]
for i, (k, v) in enumerate(intro, start=1):
    ws.cell(row=i, column=1, value=k).font = Font(name=FONT, bold=True, size=10)
    c = ws.cell(row=i, column=2, value=v)
    c.font = BODY
    c.alignment = WRAP
ws.column_dimensions["A"].width = 24
ws.column_dimensions["B"].width = 110

# ---------------------------------------------------------------- 3 Impact Evaluation
ws = wb.create_sheet("Impact Evaluation")
hdr = ["Value", "Impact level", "Impact definition", "Impact range / total loss (EUR)"]
for j, h in enumerate(hdr, 1):
    ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 4)
impact = [
    (1, "Insignificant", "Negligible negative impact on business, financial position, profit and cash flows", "0 to 199,999"),
    (2, "Minor", "Limited negative impact on business, financial position, profit and cash flows", "200,000 to 999,999"),
    (3, "Moderate", "Some potential negative impact on business, financial position, profit and cash flows", "1,000,000 to 4,999,999"),
    (4, "Major", "Considerable negative impact on business, financial position, profit and cash flows", "5,000,000 to 24,999,999"),
    (5, "Business Critical", "Detrimental negative impact on business, financial position, profit and cash flows", "25,000,000 and higher"),
]
for i, row in enumerate(impact, start=2):
    for j, v in enumerate(row, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 2, 6, 4)
for col, w in zip("ABCD", (8, 18, 70, 28)):
    ws.column_dimensions[col].width = w

# ---------------------------------------------------------------- 4 Probability Evaluation
ws = wb.create_sheet("Probability Evaluation")
for j, h in enumerate(["Value", "Level", "Description"], 1):
    ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 3)
prob = [
    (1, "Remote", "The probability of such an event is 1% to 19%"),
    (2, "Unlikely", "The probability of such an event is 20% to 39%"),
    (3, "Likely", "The probability of such an event is 40% to 59%"),
    (4, "Highly Likely", "The probability of such an event is 60% to 79%"),
    (5, "Near Certainty", "The probability of such an event is 80% to 99%"),
]
for i, row in enumerate(prob, start=2):
    for j, v in enumerate(row, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 2, 6, 3)
for col, w in zip("ABC", (8, 18, 50)):
    ws.column_dimensions[col].width = w

# ---------------------------------------------------------------- 5 Time Horizon
ws = wb.create_sheet("Time Horizon")
ws["A1"] = ("The time horizon is the third attribute used to prioritize a risk after impact and probability. "
            "Short term 0 to 3 months. Medium term 3 to 12 months. Long term more than 12 months. "
            "The matrix gives relative priority; 1 is highest.")
ws["A1"].font = BODY
ws["A1"].alignment = WRAP
ws.merge_cells("A1:D1")
ws.row_dimensions[1].height = 60
for j, h in enumerate(["Horizon", "Low", "Medium", "High"], 1):
    ws.cell(row=3, column=j, value=h)
style_header(ws, 3, 4)
for i, row in enumerate([("Short term", 5, 2, 1), ("Medium term", 7, 4, 3), ("Long term", 9, 8, 6)], start=4):
    for j, v in enumerate(row, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 4, 6, 4)
for j, h in enumerate(["Value used in register", "Horizon"], 1):
    ws.cell(row=8, column=j, value=h)
style_header(ws, 8, 2)
for i, row in enumerate([(1, "Short term"), (2, "Medium term"), (3, "Long term")], start=9):
    ws.cell(row=i, column=1, value=row[0])
    ws.cell(row=i, column=2, value=row[1])
body(ws, 9, 11, 2)
ws["A13"] = ("Fixture note: the source workbook did not state how the register's Time Horizon column is encoded "
             "(values 2 to 4 were observed against a three-band scale). This fixture uses 1 to 3 as above. "
             "Open investigation item.")
ws["A13"].font = BODY
ws["A13"].alignment = WRAP
ws.merge_cells("A13:D13")
ws.row_dimensions[13].height = 45
for col, w in zip("ABCD", (24, 12, 12, 12)):
    ws.column_dimensions[col].width = w

# ---------------------------------------------------------------- 6 Control Evaluation
ws = wb.create_sheet("Control Evaluation")
for j, h in enumerate(["Value", "Level", "Description"], 1):
    ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 3)
ctrl = [
    (1, "Effective", "Controls and management activities are properly designed and operating as intended. Regular monitoring and reporting of the risk is in place."),
    (2, "Limited improvement needed", "Controls are properly designed and operating, with some opportunities to improve efficiency and effectiveness. Some monitoring and reporting of the risk is in place."),
    (3, "Moderate improvement needed", "Key controls are in place with significant opportunities for improvement identified. Some monitoring and reporting of the risk is in place."),
    (4, "Significant improvement needed", "Limited controls are in place and a high level of risk remains. Monitoring and reporting of risks is not in place."),
    (5, "Ineffective", "Controls are not in place or have major deficiencies and are not operating as intended. Monitoring and reporting of risks is not in place."),
]
for i, row in enumerate(ctrl, start=2):
    for j, v in enumerate(row, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 2, 6, 3)
for col, w in zip("ABC", (8, 30, 90)):
    ws.column_dimensions[col].width = w

# ---------------------------------------------------------------- 7 Risk Levels
ws = wb.create_sheet("Risk Levels")
ws["A1"] = "Risk = Probability x Impact. Band edges: 1 to 6 Low, 7 to 14 Medium, 15 to 25 High."
ws["A1"].font = Font(name=FONT, bold=True, size=10)
ws.merge_cells("A1:F1")
ws.cell(row=3, column=1, value="Probability \\ Impact")
for j, lab in enumerate(["1 Insignificant", "2 Minor", "3 Moderate", "4 Major", "5 Business Critical"], start=2):
    ws.cell(row=3, column=j, value=lab)
style_header(ws, 3, 6)
plabels = ["5 (80-99%)", "4 (60-79%)", "3 (40-59%)", "2 (20-39%)", "1 (1-19%)"]
for i, (p, lab) in enumerate(zip([5, 4, 3, 2, 1], plabels), start=4):
    ws.cell(row=i, column=1, value=lab).font = Font(name=FONT, bold=True, size=10)
    for j, imp in enumerate(range(1, 6), start=2):
        c = ws.cell(row=i, column=j, value=f"={p}*{imp}")
        v = p * imp
        c.fill = PatternFill("solid", fgColor="C6EFCE" if v <= 6 else ("FFEB9C" if v <= 14 else "FFC7CE"))
        c.font = BODY
        c.border = BORDER
        c.alignment = Alignment(horizontal="center")
for j, h in enumerate(["Band", "Lower", "Upper"], 1):
    ws.cell(row=11, column=j, value=h)
style_header(ws, 11, 3)
for i, row in enumerate([("Low Risk", 1, 6), ("Medium Risk", 7, 14), ("High Risk", 15, 25)], start=12):
    for j, v in enumerate(row, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 12, 14, 3)
ws["A16"] = "Risk acceptance criteria (client-stated): residual Low and Medium are acceptable; High is not."
ws["A16"].font = BODY
ws["A16"].fill = INPUT_FILL
ws.merge_cells("A16:F16")
ws.column_dimensions["A"].width = 22
for col in "BCDEF":
    ws.column_dimensions[col].width = 18

# ---------------------------------------------------------------- 8 AI Risk Assessment (master)
ws = wb.create_sheet("AI Risk Assessment")

# Group header row (row 1) and column header row (row 2)
cols = [
    # (header, width, kind) kind: in=client input, f=formula, u=uofa added
    ("Risk #", 10, "in"),
    ("Risk Name", 22, "in"),
    ("Description", 40, "in"),
    ("Impact (1-5)", 9, "in"),
    ("Inherent Probability (1-5)", 11, "in"),
    ("Time Horizon (1-3)", 10, "in"),
    ("Inherent Calculation", 11, "f"),
    ("Inherent Risk", 13, "f"),
    ("Treatment Option", 12, "in"),
    ("Control Framework Mapping", 18, "in"),
    ("Expected Controls / Actions", 50, "in"),
    ("Existing Controls", 60, "in"),
    ("Control Effectiveness (1-5)", 11, "in"),
    ("Control Effectiveness Label", 24, "f"),
    ("Current Probability (1-5)", 11, "in"),
    ("Current Calculation", 11, "f"),
    ("Residual Risk (current)", 14, "f"),
    ("Treatment Option (current)", 12, "in"),
    ("Risk Treatment Plan", 45, "in"),
    ("Treatment Estimated Completion", 13, "in"),
    ("Probability After Treatment (1-5)", 11, "in"),
    ("Residual Calculation", 11, "f"),
    ("Residual Risk After Treatment", 14, "f"),
    ("Within Acceptance Criteria", 11, "f"),
    ("Risk Owner (acceptor)", 18, "in"),
    # UofA additions
    ("Existing Control Evidence Ref", 42, "u"),
    ("Control Type", 13, "u"),
    ("Self-Declared Gap", 10, "u"),
    ("Control Owner", 18, "u"),
    ("Treatment Completed Date", 13, "u"),
    ("Treatment Completion Evidence Ref", 42, "u"),
    ("Row Last Reviewed", 13, "u"),
    ("Days Overdue", 10, "f"),
    ("Residual Earned", 10, "f"),
    ("Acceptor Independent", 11, "f"),
]
groups = [
    ("RISK EVALUATION (inherent)", 1, 10),
    ("RISK AND CONTROL ANALYSIS", 11, 12),
    ("RISK TREATMENT (current state)", 13, 21),
    ("RESIDUAL RISK ACCEPTANCE", 22, 25),
    ("UOFA ONBOARDING COLUMNS (from evidence bundle)", 26, 32),
    ("DERIVED CHECKS", 33, 35),
]
for name, c1, c2 in groups:
    ws.cell(row=1, column=c1, value=name)
    ws.merge_cells(start_row=1, start_column=c1, end_row=1, end_column=c2)
style_header(ws, 1, len(cols))
for j, (h, w, kind) in enumerate(cols, start=1):
    ws.cell(row=2, column=j, value=h)
    ws.column_dimensions[get_column_letter(j)].width = w
style_header(ws, 2, len(cols))
for j, (h, w, kind) in enumerate(cols, start=1):
    if kind == "u":
        ws.cell(row=2, column=j).fill = PatternFill("solid", fgColor="548235")
ws.row_dimensions[2].height = 45
ws.freeze_panes = "C3"

D = dt.date
# Each row: dict of column values. Seeded defects noted in the comment field.
R = []

def row(**k):
    R.append(k)

row(id="AFR-001", name="Training Data Poisoning",
    desc="Altering labeled survey-response data to manipulate classifier behavior.",
    imp=5, p0=3, th=2, opt="Mitigate", cf="AIC-4; AIC-15; AC-2",
    exp="- Detect and remove or remediate poisoned or sensitive data in training and evaluation sets.\n"
        "- Integrity-protect data, models and code used to build models, in development and deployment.\n"
        "- Inventory and track all datasets, code, models and transformation tools.",
    exist="Annotation agreement check:\nControl: Inter-annotator agreement is computed on every labeling batch and batches under "
          "the threshold are re-labeled before use.\nModel test gate:\nControl: Candidate models must pass the benchmark "
          "suite before promotion.\nVerification:\nControl: There is currently no automated integrity verification of "
          "training inputs; the team relies on the established labeling process.",
    ce=1, p1=1, opt1="Accept", plan="N/A - Residual risk is low", due=None, p2=1, owner="R. Okafor",
    ev="evidence/labeling/agreement-report-2025Q4.pdf#sha256:3f9c...", ctype="Mandated", gap="Yes",
    cowner="R. Okafor", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D2 EFFECTIVENESS-CONTRADICTED: rated Effective (1) while the control text declares no integrity verification. "
         "D5 ACCEPTOR-NOT-INDEPENDENT: acceptor equals control owner.")

row(id="AFR-002", name="Model Source Tampering",
    desc="Tampering with model training code or weights to introduce vulnerabilities or leak IP.",
    imp=5, p0=3, th=2, opt="Mitigate", cf="RA-5; SR-9; CM-3",
    exp="- Minimize internal access to models, weights and datasets in storage and production.\n"
        "- Integrity-protect data, models and code in development and deployment.\n"
        "- Use secure-by-default frameworks and hardware for AI development.",
    exist="Code:\nControl: Inference code is versioned in the source repository, every change is reviewed, and only the "
          "main branch deploys.\nModel:\nControl: Weights are handed from the science team to platform by a shared "
          "object-storage bucket; transfers are infrequent and manual.\nAccess:\nControl: Bucket access is limited to the "
          "ML platform group.",
    ce=3, p1=3, opt1="Mitigate", plan="Implement a model registry with signed artifacts and provenance records. "
                                      "Owner: platform lead. See Risk Treatment Plans workbook, tab 'Model Source Tampering'.",
    due=D(2025, 12, 31), p2=2, owner="R. Okafor",
    ev="evidence/scm/branch-protection-export-2025-11.json#sha256:9a21...", ctype="Mandated", gap="No",
    cowner="R. Okafor", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D1 TREATMENT-OVERDUE: due 2025-12-31, no completion date or evidence, residual after treatment still claimed as Medium 10. "
         "D5 ACCEPTOR-NOT-INDEPENDENT.")

row(id="AFR-003", name="Model Deployment Tampering",
    desc="Unauthorized changes to deployed model components or serving configuration.",
    imp=4, p0=3, th=2, opt="Mitigate", cf="CM-3; SR-9",
    exp="- Use secure-by-default frameworks, libraries and hardware for deployment.\n"
        "- Enforce reviewed, auditable release of every production model.",
    exist="Deployment tool:\nControl: All production models deploy through the internal CLI deployment tool, which runs "
          "validation steps.\nVerification:\nControl: No automated verification during inference; the team relies on "
          "the deployment process.",
    ce=2, p1=2, opt1="Mitigate", plan="Mature the AI CI/CD pipeline: signed images, admission check on model hash. "
                                      "See Comprehensive Risk Treatment Plan.",
    due=D(2026, 3, 31), p2=1, owner="R. Okafor",
    ev="evidence/cicd/mdt-run-log-2026-02-14.txt#sha256:71be...", ctype="Mandated", gap="Yes",
    cowner="J. Lindqvist", done=D(2026, 3, 20), doneev="evidence/cicd/admission-policy-v2.yaml#sha256:c0d4...",
    reviewed=D(2026, 3, 20),
    note="Clean on treatment: completed before due date with evidence. D2 EFFECTIVENESS-CONTRADICTED at rating 2 with a declared gap. "
         "Acceptor is independent of control owner.")

row(id="AFR-004", name="Prompt Denial of Service",
    desc="Overloading LLM endpoints with resource-intensive queries.",
    imp=4, p0=3, th=1, opt="Mitigate", cf="AIC-8; CP-2",
    exp="- Block or rate-limit adversarial and resource-intensive queries to AI models.",
    exist="Central LLM gateway:\nControl: All LLM traffic passes through one gateway with per-tenant rate limits and "
          "token budgets.",
    ce=1, p1=1, opt1="Accept", plan="N/A - Residual risk is low", due=None, p2=1, owner="M. Duarte",
    ev="evidence/gateway/rate-limit-config-prod-2026-01.json#sha256:0e7a...", ctype="Mandated", gap="No",
    cowner="J. Lindqvist", done=None, doneev="", reviewed=D(2026, 1, 10),
    note="Negative control: clean row. No firings expected.")

row(id="AFR-005", name="Prompt Injection",
    desc="Compromising an LLM feature's output by manipulating the input prompt.",
    imp=5, p0=3, th=1, opt="Mitigate", cf="AIC-4; AIC-15",
    exp="- Block, nullify or sanitize insecure output before it reaches applications or users.\n"
        "- Make models robust to adversarial inputs in the context of their use.",
    exist="Vendor guardrails:\nControl: Input and output pass through the vendor's built-in content guardrails.\n"
          "Launch review:\nControl: New features do not use the gateway guardrails by default; a manual launch readiness "
          "review decides which guardrails a feature needs before release.",
    ce=3, p1=3, opt1="Mitigate", plan="Update the launch readiness policy so guardrails apply from early access onward. "
                                      "Owner: science lead.",
    due=D(2025, 9, 30), p2=2, owner="R. Okafor",
    ev="", ctype="Mandated", gap="No",
    cowner="S. Varga", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D1 TREATMENT-OVERDUE: due 2025-09-30, nothing recorded. D4 CONTROL-UNEVIDENCED: no evidence ref for the guardrail claim.")

row(id="AFR-006", name="Unintended Model Output",
    desc="Unvalidated, harmful or unintended outputs passed to users.",
    imp=4, p0=3, th=2, opt="Mitigate", cf="AIC-4; AIC-15",
    exp="- Make models robust to adversarial inputs.\n- Sanitize output before it reaches users.",
    exist="Grounding checks:\nControl: Output grounding is validated against the retrieved context.\nRed-teaming:\n"
          "Control: Features flagged in launch review are red-teamed before release.\nDocumentation:\nControl: "
          "Evaluation methods and metrics are recorded in the model risk card.",
    ce=2, p1=2, opt1="Mitigate", plan="Publish output-guardrail and model-validation documentation. Owner: science lead.",
    due=D(2025, 7, 18), p2=1, owner="R. Okafor",
    ev="evidence/mrm/model-risk-card-topicsummarizer-v3.pdf#sha256:5d10...", ctype="Mandated", gap="No",
    cowner="S. Varga", done=D(2025, 7, 16), doneev="evidence/mrm/output-guardrails-standard-v1.pdf#sha256:88af...",
    reviewed=D(2025, 7, 16),
    note="Negative control: treatment completed with evidence, control evidenced. No firings expected.")

row(id="AFR-007", name="Excessive Data Handling",
    desc="Unauthorized collection, retention, processing or sharing of user data in AI features.",
    imp=5, p0=3, th=2, opt="Mitigate", cf="AIC-10; AIC-10(1)",
    exp="- Store, process and use prompts and logs in line with user consent.\n"
        "- Inform users of relevant AI risks and give transparency and control over their data.",
    exist="Consent:\nControl: Product management obtains written customer consent before raw data is used for a proof "
          "of concept.\nStorage:\nControl: Raw customer data is held in encrypted buckets with a 30-day time to live.",
    ce=3, p1=3, opt1="Mitigate", plan="Stand up the experimentation platform so POC data never leaves governed storage. "
                                      "See Risk Treatment Plans workbook, tab 'Excessive Data Handling'.",
    due=D(2026, 3, 31), p2=2, owner="R. Okafor",
    ev="evidence/storage/bucket-lifecycle-policy-2025-11.json#sha256:ab33...", ctype="Mandated", gap="No",
    cowner="R. Okafor", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D1 TREATMENT-OVERDUE. D5 ACCEPTOR-NOT-INDEPENDENT.")

row(id="AFR-008", name="Fairness and Bias",
    desc="Models produce unreasonable levels of bias in their responses.",
    imp=5, p0=4, th=2, opt="Mitigate", cf="AIC-5; AIC-5(1)",
    exp="- Collect diverse and representative data; detect and measure bias with statistical fairness metrics.\n"
        "- Audit outputs for bias before deployment and in operation; keep a human in the loop.",
    exist="Science launch sign-off:\nControl: A checklist gates launch approval.\nBias testing:\nControl: Project leads "
          "decide whether to run bias and fairness testing on a case-by-case basis, when an obvious need is identified.",
    ce=4, p1=4, opt1="Mitigate", plan="Assess and implement a third-party fairness evaluation tool. "
                                      "See Risk Treatment Plans workbook, tab 'Fairness and Bias'.",
    due=D(2025, 11, 30), p2=2, owner="R. Okafor",
    ev="evidence/launch/science-signoff-checklist-template.docx#sha256:12cc...", ctype="Discretionary", gap="No",
    cowner="S. Varga", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D3 CONTROL-DISCRETIONARY: bias testing runs at project-lead discretion. D1 TREATMENT-OVERDUE. "
         "Effectiveness 4 is consistent with the text, so no contradiction firing.")

row(id="AFR-009", name="Regulatory Non-Compliance",
    desc="Non-compliance with applicable data protection regulation in AI processing.",
    imp=5, p0=2, th=2, opt="Mitigate", cf="AIC-10; AIC-10(1)",
    exp="- Map AI processing activities to the records of processing; run privacy impact assessments.",
    exist="Privacy review:\nControl: Every AI feature passes a privacy impact assessment before launch; the record "
          "is filed with the privacy office.",
    ce=1, p1=1, opt1="Accept", plan="N/A - Residual risk is low", due=None, p2=1, owner="L. Brennan",
    ev="evidence/privacy/pia-register-export-2026-01.csv#sha256:e4e4...", ctype="Mandated", gap="No",
    cowner="L. Brennan", done=None, doneev="", reviewed=D(2026, 1, 10),
    note="D5 ACCEPTOR-NOT-INDEPENDENT only (privacy lead owns and accepts).")

row(id="AFR-010", name="Supply Chain Vulnerabilities",
    desc="Third-party model and library dependencies introduce security or availability risk.",
    imp=4, p0=3, th=2, opt="Mitigate", cf="SR-2(1); SR-6; SR-9",
    exp="- Run a vendor risk program for AI component suppliers.\n- Diversify suppliers for critical components.",
    exist="Vendor-agnostic gateway:\nControl: A unified API supports several LLM providers so traffic can move between "
          "them.\nDependencies:\nControl: Base images and open-source libraries are scanned by the vulnerability "
          "management system.",
    ce=2, p1=2, opt1="Mitigate", plan="Implement inference zones with per-zone provider failover. "
                                      "See supply chain assessment (AFR-010).",
    due=D(2025, 9, 30), p2=1, owner="M. Duarte",
    ev="evidence/vuln/scan-summary-ml-images-2026-02.pdf#sha256:7b7b...", ctype="Mandated", gap="No",
    cowner="J. Lindqvist", done=D(2025, 9, 28), doneev="evidence/gateway/inference-zones-release-notes-1.4.md#sha256:2f2f...",
    reviewed=D(2025, 10, 1),
    note="Negative control: clean row.")

row(id="AFR-011", name="Inadequate User Training",
    desc="Staff lacking training misuse AI tools.",
    imp=3, p0=4, th=2, opt="Mitigate", cf="AT-3",
    exp="- Role-specific training for all users of AI tools, with refreshers.",
    exist="Training:\nControl: Annual AI training for engineers at three levels, plus security and privacy training. "
          "Scientists get role-based training on the model risk process.",
    ce=3, p1=3, opt1="Mitigate", plan="Add an AI awareness section to annual and new-hire security training.",
    due=D(2025, 6, 30), p2=1, owner="D. Tanaka",
    ev="", ctype="Mandated", gap="No",
    cowner="D. Tanaka", done=D(2025, 6, 25), doneev="",
    reviewed=D(2025, 7, 1),
    note="D4 CONTROL-UNEVIDENCED: training claim has no completion-record export. Treatment marked done but with no "
         "completion evidence, so Residual Earned is No. D5 ACCEPTOR-NOT-INDEPENDENT.")

row(id="AFR-012", name="Data Anonymization Not Followed",
    desc="Standard anonymization process skipped, so identifiable data is used to fine-tune models.",
    imp=5, p0=4, th=2, opt="Mitigate", cf="AIC-14",
    exp="- Audit adherence to the anonymization standard for all data used in model development.\n"
        "- Automate anonymization checks in the data pipeline.",
    exist="Manual anonymization process:\nControl: Science team members are trained on anonymization and aggregation; "
          "adherence depends on individual project leads.",
    ce=4, p1=4, opt1="Mitigate", plan="Fully implement the unified data studio with enforced anonymization. "
                                      "See Risk Treatment Plans workbook, tab 'Data Anonymization'.",
    due=D(2025, 12, 31), p2=2, owner="R. Okafor",
    ev="evidence/training/anonymization-course-roster-2025.csv#sha256:9d9d...", ctype="Discretionary", gap="No",
    cowner="S. Varga", done=None, doneev="", reviewed=D(2025, 6, 15),
    note="D3 CONTROL-DISCRETIONARY. D1 TREATMENT-OVERDUE.")

row(id="AFR-013", name="Third-Party Availability",
    desc="Third-party LLM services unavailable due to provider outage.",
    imp=4, p0=2, th=2, opt="Mitigate", cf="SR-2(1); SR-6",
    exp="- Multi-provider failover; graceful degradation of optional AI features.",
    exist="Gateway resilience:\nControl: The inference gateway retries against alternate deployments on failure; "
          "consuming services degrade gracefully.",
    ce=1, p1=1, opt1="Accept", plan="N/A - Residual risk is low", due=None, p2=1, owner="M. Duarte",
    ev="evidence/gateway/failover-drill-2026-02-03.md#sha256:4c4c...", ctype="Mandated", gap="No",
    cowner="J. Lindqvist", done=None, doneev="", reviewed=D(2026, 2, 3),
    note="Negative control: clean row.")

first = 3
for i, r in enumerate(R):
    n = first + i
    vals = {
        1: r["id"], 2: r["name"], 3: r["desc"], 4: r["imp"], 5: r["p0"], 6: r["th"],
        7: f"=D{n}*E{n}",
        8: f'=IF(G{n}>=15,"High Risk",IF(G{n}>=7,"Medium Risk","Low Risk"))',
        9: r["opt"], 10: r["cf"], 11: r["exp"], 12: r["exist"], 13: r["ce"],
        14: f"=INDEX('Control Evaluation'!$B$2:$B$6,MATCH(M{n},'Control Evaluation'!$A$2:$A$6,0))",
        15: r["p1"],
        16: f"=D{n}*O{n}",
        17: f'=IF(P{n}>=15,"High Risk",IF(P{n}>=7,"Medium Risk","Low Risk"))',
        18: r["opt1"], 19: r["plan"], 20: r["due"], 21: r["p2"],
        22: f"=D{n}*U{n}",
        23: f'=IF(V{n}>=15,"High Risk",IF(V{n}>=7,"Medium Risk","Low Risk"))',
        24: f'=IF(W{n}="High Risk","No","Yes")',
        25: r["owner"],
        26: r["ev"], 27: r["ctype"], 28: r["gap"], 29: r["cowner"], 30: r["done"], 31: r["doneev"], 32: r["reviewed"],
        33: f'=IF(AND(T{n}<>"",AD{n}="",T{n}<\'Register Checks\'!$B$2),\'Register Checks\'!$B$2-T{n},"")',
        34: f'=IF(R{n}="Accept","n/a",IF(AND(AD{n}<>"",AE{n}<>""),"Yes","No"))',
        35: f'=IF(Y{n}=AC{n},"No","Yes")',
    }
    for c, v in vals.items():
        cell = ws.cell(row=n, column=c, value=v)
        kind = cols[c - 1][2]
        if kind == "in":
            cell.fill = INPUT_FILL
        elif kind == "u":
            cell.fill = UOFA_FILL
        if c in (20, 30, 32):
            cell.number_format = "yyyy-mm-dd"
    ws.cell(row=n, column=1).comment = Comment(r["note"], "fixture")
    # source comments on the UofA cells, as `uofa extract` would write them
    if r["ev"]:
        ws.cell(row=n, column=26).comment = Comment(
            f"extract: pointer found in bundle; confidence 0.9; source {r['ev'].split('#')[0]}", "uofa extract")
    ws.cell(row=n, column=27).comment = Comment(
        "extract: classified from Existing Controls text; Discretionary when the text says the control runs "
        "'case-by-case', 'when needed', or 'depends on' a person.", "uofa extract")
    ws.cell(row=n, column=28).comment = Comment(
        "extract: Yes when Existing Controls text contains a stated absence ('no automated', 'not currently', "
        "'relies solely on').", "uofa extract")
last = first + len(R) - 1
body(ws, 3, last, len(cols))
for n in range(3, last + 1):
    for c in range(1, len(cols) + 1):
        kind = cols[c - 1][2]
        if kind == "in":
            ws.cell(row=n, column=c).fill = INPUT_FILL
        elif kind == "u":
            ws.cell(row=n, column=c).fill = UOFA_FILL
    ws.row_dimensions[n].height = 150

# validations
dv_15 = DataValidation(type="whole", operator="between", formula1=1, formula2=5, allow_blank=True)
dv_13 = DataValidation(type="whole", operator="between", formula1=1, formula2=3, allow_blank=True)
dv_opt = DataValidation(type="list", formula1='"Mitigate,Accept,Avoid,Transfer"', allow_blank=True)
dv_ctype = DataValidation(type="list", formula1='"Mandated,Discretionary"', allow_blank=True)
dv_yn = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
for dv in (dv_15, dv_13, dv_opt, dv_ctype, dv_yn):
    ws.add_data_validation(dv)
rng = f"3:{last + 50}"
for col in ("D", "E", "M", "O", "U"):
    dv_15.add(f"{col}3:{col}{last + 50}")
dv_13.add(f"F3:F{last + 50}")
dv_opt.add(f"I3:I{last + 50}")
dv_opt.add(f"R3:R{last + 50}")
dv_ctype.add(f"AA3:AA{last + 50}")
dv_yn.add(f"AB3:AB{last + 50}")

# ---------------------------------------------------------------- 9 Register Checks
ws = wb.create_sheet("Register Checks")
reg = "'AI Risk Assessment'"
rr = f"$3:${last}"
ws["A1"] = "Register verification summary (computed; reviewer reads this first)"
ws["A1"].font = Font(name=FONT, bold=True, size=11)
ws["A2"] = "Assessment date"
ws["B2"] = TODAY
ws["B2"].number_format = "yyyy-mm-dd"
ws["B2"].fill = INPUT_FILL
ws["C2"] = "Set to the date of the review. Days Overdue and the staleness check key off this cell."
ws["A3"] = "Register next review date"
ws["B3"] = "='Document Control'!B9"
ws["B3"].number_format = "yyyy-mm-dd"
ws["A4"] = "Register past its review date"
ws["B4"] = '=IF(B3<B2,"Yes","No")'
ws["C4"] = "W-AIMS-REGISTER-STALE"

checks = [
    ("Rows in register", f"=COUNTA({reg}!A{rr.replace('$','')})".replace(f"A3:{last}", f"A3:A{last}"), ""),
    ("Residuals resting on a treatment that is overdue with no completion",
     f'=COUNTIFS({reg}!AG3:AG{last},">0")', "W-AIMS-TREATMENT-OVERDUE. The headline number."),
    ("Mitigate rows whose residual after treatment is not earned (no completion evidence)",
     f'=COUNTIF({reg}!AH3:AH{last},"No")', "W-AIMS-RESIDUAL-UNEARNED"),
    ("Existing Controls with no evidence reference",
     f'=COUNTBLANK({reg}!Z3:Z{last})', "W-AIMS-CONTROL-UNEVIDENCED"),
    ("Controls recorded as Discretionary",
     f'=COUNTIF({reg}!AA3:AA{last},"Discretionary")', "W-AIMS-CONTROL-DISCRETIONARY"),
    ("Effectiveness 1 or 2 with a self-declared gap in the control text",
     f'=COUNTIFS({reg}!M3:M{last},"<=2",{reg}!AB3:AB{last},"Yes")', "W-AIMS-EFFECTIVENESS-CONTRADICTED"),
    ("Rows where the acceptor is also the control owner",
     f'=COUNTIF({reg}!AI3:AI{last},"No")', "W-AIMS-ACCEPTOR-NOT-INDEPENDENT"),
    ("Rows rated High residual after treatment (outside acceptance criteria)",
     f'=COUNTIF({reg}!X3:X{last},"No")', "Acceptance criteria breach"),
]
checks[0] = ("Rows in register", f"=COUNTA({reg}!A3:A{last})", "")
for j, h in enumerate(["Check", "Count", "Pattern / note"], 1):
    ws.cell(row=6, column=j, value=h)
style_header(ws, 6, 3)
for i, (label, f, note) in enumerate(checks, start=7):
    ws.cell(row=i, column=1, value=label)
    ws.cell(row=i, column=2, value=f)
    ws.cell(row=i, column=3, value=note)
body(ws, 7, 6 + len(checks), 3)
for r in range(2, 5):
    for c in range(1, 4):
        ws.cell(row=r, column=c).font = BODY
ws.column_dimensions["A"].width = 70
ws.column_dimensions["B"].width = 14
ws.column_dimensions["C"].width = 60

# ---------------------------------------------------------------- 10 Seeded Defects
ws = wb.create_sheet("Seeded Defects")
for j, h in enumerate(["Defect", "Proposed pattern id", "Rows", "What fires it", "Column(s) the rule reads"], 1):
    ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 5)
defects = [
    ("D1", "W-AIMS-TREATMENT-OVERDUE", "AFR-002, 005, 007, 008, 012",
     "Treatment Estimated Completion is before the assessment date and Treatment Completed Date is blank, while "
     "Probability After Treatment and the residual band are still claimed.",
     "T, AD, U, W"),
    ("D2", "W-AIMS-EFFECTIVENESS-CONTRADICTED", "AFR-001, 003",
     "Control Effectiveness is 1 or 2 and Self-Declared Gap is Yes.", "M, AB"),
    ("D3", "W-AIMS-CONTROL-DISCRETIONARY", "AFR-008, 012",
     "Control Type is Discretionary. The register records a practice that nobody is required to run as a control.",
     "AA"),
    ("D4", "W-AIMS-CONTROL-UNEVIDENCED", "AFR-005, 011",
     "Existing Controls text is present and Existing Control Evidence Ref is blank.", "L, Z"),
    ("D5", "W-AIMS-ACCEPTOR-NOT-INDEPENDENT", "AFR-001, 002, 007, 009, 011",
     "Risk Owner (acceptor) equals Control Owner.", "Y, AC"),
    ("D6", "W-AIMS-REGISTER-STALE", "whole register",
     "Document Control next review date is before the assessment date.", "'Document Control'!B9"),
    ("D7", "W-AIMS-RESIDUAL-UNEARNED", "AFR-011 plus every D1 row",
     "Mitigate row with no completion evidence reference; covers the case where a completion date was typed "
     "but nothing backs it.", "R, AD, AE"),
    ("Clean", "none", "AFR-004, 006, 010, 013",
     "Negative controls. A rule that fires on these is over-firing.", ""),
]
for i, row_ in enumerate(defects, start=2):
    for j, v in enumerate(row_, 1):
        ws.cell(row=i, column=j, value=v)
body(ws, 2, 1 + len(defects), 5)
for col, w in zip("ABCDE", (8, 36, 28, 80, 22)):
    ws.column_dimensions[col].width = w

wb.save(OUT)
print("saved", OUT)
