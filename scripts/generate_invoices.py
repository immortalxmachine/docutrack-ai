"""
Generate clearly-labelled SAMPLE commercial-invoice PDFs for the
/extract-invoice demo.

These are deliberately **not** made to look like a real company's paperwork.
Every party name is an obvious placeholder ("Sample Exporter 1 (fictitious)"),
and each page carries a bold "SAMPLE — fictitious data, demo use only" banner
and footer. The *structure* of a commercial invoice is real (shipper,
consignee, HS-coded line items, declared value) so the extraction + SQL-summary
path can be exercised end-to-end; the *data* is fictitious on purpose.

HS codes and destination countries are drawn from public classification
examples so that /invoices/summary aggregates (value by country, top HS codes)
are non-trivial, but no real importer/exporter is represented.

Run:
    python -m scripts.generate_invoices
Output:
    data/invoices/*.pdf   (5 sample invoices)
"""
from __future__ import annotations

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BANNER_TEXT = "SAMPLE INVOICE — fictitious data, created for the DocuTrack AI demo. Not a real commercial invoice."
FOOTER_TEXT = "SAMPLE — fictitious data, demo use only. Not a real commercial invoice."

# Each invoice: metadata + line items. Party names are obvious placeholders;
# HS codes / countries are realistic so the SQL aggregates are meaningful.
# The declared-value total is computed from the line items at render time.
INVOICES: list[dict] = [
    {
        "number": "SAMPLE-0001",
        "date": "2025-03-14",
        "currency": "USD",
        "shipper": {"name": "Sample Exporter 1 (fictitious)", "address": "1 Demo Street, Sample City, India", "country": "India"},
        "consignee": {"name": "Demo Importer A (fictitious)", "address": "100 Example Ave, Sample Town, USA", "country": "United States"},
        "items": [
            {"description": "Cotton bed sheets, queen size", "hs_code": "630231", "qty": 200, "unit_price": 12.50},
            {"description": "Cotton pillow covers", "hs_code": "630240", "qty": 400, "unit_price": 3.20},
        ],
    },
    {
        "number": "SAMPLE-0002",
        "date": "2025-04-02",
        "currency": "GBP",
        "shipper": {"name": "Sample Exporter 2 (fictitious)", "address": "2 Demo Street, Sample City, India", "country": "India"},
        "consignee": {"name": "Demo Importer B (fictitious)", "address": "200 Example Ave, Sample Town, UK", "country": "United Kingdom"},
        "items": [
            {"description": "Servo motor assemblies", "hs_code": "850132", "qty": 50, "unit_price": 85.00},
            {"description": "Motor controller boards", "hs_code": "853710", "qty": 50, "unit_price": 40.00},
        ],
    },
    {
        "number": "SAMPLE-0003",
        "date": "2025-05-21",
        "currency": "EUR",
        "shipper": {"name": "Sample Exporter 3 (fictitious)", "address": "3 Demo Street, Sample City, India", "country": "India"},
        "consignee": {"name": "Demo Importer C (fictitious)", "address": "300 Example Ave, Sample Town, Germany", "country": "Germany"},
        "items": [
            {"description": "Black pepper, whole", "hs_code": "090411", "qty": 500, "unit_price": 6.80},
            {"description": "Cardamom pods, green", "hs_code": "090831", "qty": 120, "unit_price": 18.00},
            {"description": "Turmeric powder", "hs_code": "091030", "qty": 300, "unit_price": 4.10},
        ],
    },
    {
        "number": "SAMPLE-0004",
        "date": "2025-06-09",
        "currency": "USD",
        "shipper": {"name": "Sample Exporter 4 (fictitious)", "address": "4 Demo Street, Sample City, India", "country": "India"},
        "consignee": {"name": "Demo Importer D (fictitious)", "address": "400 Example Ave, Sample Town, UAE", "country": "United Arab Emirates"},
        "items": [
            {"description": "Sterile surgical gloves (box of 100)", "hs_code": "401511", "qty": 800, "unit_price": 5.50},
            {"description": "Disposable syringes 5ml", "hs_code": "901831", "qty": 1000, "unit_price": 0.90},
        ],
    },
    {
        "number": "SAMPLE-0005",
        "date": "2025-07-18",
        "currency": "USD",
        "shipper": {"name": "Sample Exporter 5 (fictitious)", "address": "5 Demo Street, Sample City, India", "country": "India"},
        "consignee": {"name": "Demo Importer E (fictitious)", "address": "500 Example Ave, Sample Town, Singapore", "country": "Singapore"},
        "items": [
            {"description": "Leather handbags", "hs_code": "420221", "qty": 150, "unit_price": 34.00},
            {"description": "Leather wallets", "hs_code": "420231", "qty": 300, "unit_price": 9.75},
        ],
    },
]


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillGray(0.5)
    canvas.drawCentredString(A4[0] / 2.0, 1.2 * cm, FOOTER_TEXT)
    canvas.restoreState()


def _party_block(label: str, party: dict, style) -> Paragraph:
    text = f"<b>{label}</b><br/>{party['name']}<br/>{party['address']}<br/>Country: {party['country']}"
    return Paragraph(text, style)


def _build(spec: dict, out_dir: str) -> tuple[str, float]:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvTitle", parent=styles["Title"], fontSize=20, spaceAfter=4)
    banner_style = ParagraphStyle(
        "InvBanner", parent=styles["BodyText"], fontSize=9, leading=12,
        textColor=colors.white, backColor=colors.HexColor("#b71c1c"),
        borderPadding=4, spaceAfter=10, alignment=1,
    )
    small = ParagraphStyle("InvSmall", parent=styles["BodyText"], fontSize=10, leading=14)

    total = sum(it["qty"] * it["unit_price"] for it in spec["items"])
    cur = spec["currency"]
    path = os.path.join(out_dir, f"{spec['number']}.pdf")

    pdf = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"SAMPLE Commercial Invoice {spec['number']}",
    )

    story: list = [
        Paragraph(BANNER_TEXT, banner_style),
        Paragraph("COMMERCIAL INVOICE (SAMPLE)", title_style),
        Paragraph(f"Invoice No: <b>{spec['number']}</b> &nbsp;&nbsp; Date: {spec['date']} "
                  f"&nbsp;&nbsp; Currency: {cur}", small),
        Spacer(1, 0.4 * cm),
        _party_block("Shipper / Exporter", spec["shipper"], small),
        Spacer(1, 0.2 * cm),
        _party_block("Consignee / Importer", spec["consignee"], small),
        Spacer(1, 0.5 * cm),
    ]

    # Line-items table.
    header = ["Description", "HS Code", "Qty", f"Unit Price ({cur})", f"Amount ({cur})"]
    rows = [header]
    for it in spec["items"]:
        amount = it["qty"] * it["unit_price"]
        rows.append([it["description"], it["hs_code"], str(it["qty"]),
                     f"{it['unit_price']:.2f}", f"{amount:,.2f}"])
    rows.append(["", "", "", "Total declared value", f"{total:,.2f}"])

    table = Table(rows, colWidths=[6.5 * cm, 2.2 * cm, 1.3 * cm, 3.0 * cm, 3.0 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a148c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (-2, -1), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "SAMPLE document — the parties above are fictitious placeholders and no "
        "declaration of origin is made. For demonstration of data extraction only.", small))

    pdf.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path, total


def main() -> None:
    out_dir = os.path.join("data", "invoices")
    os.makedirs(out_dir, exist_ok=True)
    written = [_build(spec, out_dir) for spec in INVOICES]
    print(f"Wrote {len(written)} SAMPLE invoices to {out_dir}/")
    for path, total in written:
        print(f"  - {os.path.basename(path)}  (declared value {total:,.2f})")


if __name__ == "__main__":
    main()
