"""
Generate synthetic commercial-invoice PDFs for testing /extract-invoice.

Each invoice is invented, labelled synthetic in the footer, and has a layout
close to a real commercial invoice so the LLM extraction has realistic input.
The five invoices deliberately span several destination countries and HS codes
so that /invoices/summary aggregates are non-trivial.

Run:
    python -m scripts.generate_invoices
Output:
    data/invoices/*.pdf   (5 invoices)
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

FOOTER_TEXT = "Synthetic sample document — created for the DocuTrack AI project. Not a real commercial invoice."

# Each invoice: metadata + line items. Values are invented but consistent;
# the declared-value total is computed from the line items at render time.
INVOICES: list[dict] = [
    {
        "number": "INV-2025-0001",
        "date": "2025-03-14",
        "currency": "USD",
        "shipper": {"name": "Madras Textiles Pvt Ltd", "address": "12 Anna Salai, Chennai 600002, India", "country": "India"},
        "consignee": {"name": "Brooklyn Home Goods LLC", "address": "88 Flatbush Ave, New York 11217, USA", "country": "United States"},
        "items": [
            {"description": "Cotton bed sheets, queen size", "hs_code": "630231", "qty": 200, "unit_price": 12.50},
            {"description": "Cotton pillow covers", "hs_code": "630240", "qty": 400, "unit_price": 3.20},
        ],
    },
    {
        "number": "INV-2025-0002",
        "date": "2025-04-02",
        "currency": "GBP",
        "shipper": {"name": "Bengaluru Robotics Ltd", "address": "4 MG Road, Bengaluru 560001, India", "country": "India"},
        "consignee": {"name": "Manchester Automation Co", "address": "19 Deansgate, Manchester M3 2BW, UK", "country": "United Kingdom"},
        "items": [
            {"description": "Servo motor assemblies", "hs_code": "850132", "qty": 50, "unit_price": 85.00},
            {"description": "Motor controller boards", "hs_code": "853710", "qty": 50, "unit_price": 40.00},
        ],
    },
    {
        "number": "INV-2025-0003",
        "date": "2025-05-21",
        "currency": "EUR",
        "shipper": {"name": "Kochi Spice Exporters", "address": "7 Marine Drive, Kochi 682031, India", "country": "India"},
        "consignee": {"name": "Hamburg Gourmet GmbH", "address": "23 Speicherstadt, Hamburg 20457, Germany", "country": "Germany"},
        "items": [
            {"description": "Black pepper, whole", "hs_code": "090411", "qty": 500, "unit_price": 6.80},
            {"description": "Cardamom pods, green", "hs_code": "090831", "qty": 120, "unit_price": 18.00},
            {"description": "Turmeric powder", "hs_code": "091030", "qty": 300, "unit_price": 4.10},
        ],
    },
    {
        "number": "INV-2025-0004",
        "date": "2025-06-09",
        "currency": "USD",
        "shipper": {"name": "Pune Pharma Labs", "address": "55 FC Road, Pune 411004, India", "country": "India"},
        "consignee": {"name": "Gulf Medical Supplies FZE", "address": "Jebel Ali Free Zone, Dubai, UAE", "country": "United Arab Emirates"},
        "items": [
            {"description": "Sterile surgical gloves (box of 100)", "hs_code": "401511", "qty": 800, "unit_price": 5.50},
            {"description": "Disposable syringes 5ml", "hs_code": "901831", "qty": 1000, "unit_price": 0.90},
        ],
    },
    {
        "number": "INV-2025-0005",
        "date": "2025-07-18",
        "currency": "USD",
        "shipper": {"name": "Hyderabad Leather Works", "address": "3 Banjara Hills, Hyderabad 500034, India", "country": "India"},
        "consignee": {"name": "Singapore Fashion Hub Pte", "address": "10 Orchard Road, Singapore 238840", "country": "Singapore"},
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
    small = ParagraphStyle("InvSmall", parent=styles["BodyText"], fontSize=10, leading=14)

    total = sum(it["qty"] * it["unit_price"] for it in spec["items"])
    cur = spec["currency"]
    path = os.path.join(out_dir, f"{spec['number']}.pdf")

    pdf = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Commercial Invoice {spec['number']}",
    )

    story: list = [
        Paragraph("COMMERCIAL INVOICE", title_style),
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
        "I declare that the information above is true and correct. "
        "Goods are of Indian origin unless otherwise stated.", small))

    pdf.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path, total


def main() -> None:
    out_dir = os.path.join("data", "invoices")
    os.makedirs(out_dir, exist_ok=True)
    written = [_build(spec, out_dir) for spec in INVOICES]
    print(f"Wrote {len(written)} synthetic invoices to {out_dir}/")
    for path, total in written:
        print(f"  - {os.path.basename(path)}  (declared value {total:,.2f})")


if __name__ == "__main__":
    main()
