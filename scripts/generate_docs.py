"""
Generate the synthetic shipping & customs policy library.

Why synthetic? A portfolio project must not ship a real carrier's copyrighted
policies. Every document here is invented for DocuTrack AI, contains made-up
but *internally consistent and specific* facts (so retrieval + Q&A can be
evaluated against known answers), and carries a "Synthetic sample document"
footer on every page.

Run:
    python -m scripts.generate_docs
Output:
    data/docs/*.pdf   (10 documents)
"""
from __future__ import annotations

import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.config import get_settings

FOOTER_TEXT = "Synthetic sample document — created for the DocuTrack AI project. Not a real carrier policy."

# ---------------------------------------------------------------------------
# Document content.
# Each entry: filename -> {title, intro, sections:[(heading, [paragraph|•bullet])]}
# A line beginning with "• " is rendered as a bullet; everything else is a
# normal paragraph. Facts are deliberately concrete so eval has crisp answers.
# ---------------------------------------------------------------------------
DOCS: dict[str, dict] = {
    "prohibited_items.pdf": {
        "title": "Prohibited and Restricted Items Policy",
        "intro": "This policy lists items that may never be shipped (prohibited) "
        "and items that may be shipped only under stated conditions (restricted).",
        "sections": [
            (
                "1. Prohibited items (never accepted)",
                [
                    "The following items are refused at drop-off and seized if discovered in transit:",
                    "• Currency, bullion, and negotiable instruments in bearer form.",
                    "• Live animals, human remains, and perishable biological samples without a cold-chain contract.",
                    "• Illegal narcotics and items whose possession is unlawful at origin or destination.",
                    "• Loose lithium-metal batteries with more than 2 grams of lithium content.",
                    "• Lithium-ion batteries rated above 100 watt-hours when shipped by air without dangerous-goods approval.",
                ],
            ),
            (
                "2. Restricted items (conditional acceptance)",
                [
                    "These are accepted only when the stated condition is met:",
                    "• Alcoholic beverages: business-to-business only, with an adult-signature service selected.",
                    "• Firearms and parts: licensed dealers only, ground service, with a copy of the licence enclosed.",
                    "• Perishable food: double-walled packaging and a maximum transit time of 48 hours.",
                    "• Aerosols and perfumes: limited to 500 millilitres per package on ground service.",
                ],
            ),
            (
                "3. Consequences of non-compliance",
                [
                    "Packages containing prohibited items are held and reported to the relevant authority. "
                    "The shipper forfeits all transportation charges and is liable for any disposal cost. "
                    "Repeated violations lead to account suspension after three recorded incidents in twelve months.",
                ],
            ),
        ],
    },
    "packaging_guidelines.pdf": {
        "title": "Packaging Rules and Standards",
        "intro": "Correct packaging prevents damage and avoids re-packaging surcharges. "
        "These rules apply to all service levels.",
        "sections": [
            (
                "1. Box selection",
                [
                    "• Use a new, rigid, double-wall corrugated box for any shipment over 10 kilograms.",
                    "• Leave at least 5 centimetres of cushioning between the contents and every wall of the box.",
                    "• The maximum accepted girth (length plus twice width plus twice height) is 330 centimetres.",
                    "• The maximum weight for a single parcel on standard ground service is 68 kilograms.",
                ],
            ),
            (
                "2. Cushioning and sealing",
                [
                    "• Fragile items must be wrapped individually and suspended away from box corners.",
                    "• Seal all seams with pressure-sensitive plastic tape at least 48 millimetres wide using the H-taping method.",
                    "• Do not use paper wrapping, string, or twine on the outer box; these jam automated sorters.",
                ],
            ),
            (
                "3. Labelling",
                [
                    "• Place one shipping label on the largest top surface, never over a seam or corner.",
                    "• Remove or cross out all old labels and barcodes before re-using a box.",
                    "A re-packaging surcharge of 350 rupees applies when a parcel must be re-boxed at a hub to meet these rules.",
                ],
            ),
        ],
    },
    "customs_declaration_india_exports.pdf": {
        "title": "Customs Declaration Basics for India Exports",
        "intro": "This guide covers the paperwork required to export a commercial "
        "shipment from India. It is a simplified summary for small exporters.",
        "sections": [
            (
                "1. Required documents",
                [
                    "Every commercial export from India must include:",
                    "• A commercial invoice showing shipper, consignee, item description, quantity, unit value, and currency.",
                    "• A packing list describing the contents of each carton.",
                    "• The exporter's IEC (Importer-Exporter Code), a ten-digit code issued by the DGFT.",
                    "• A completed Shipping Bill filed electronically on the ICEGATE portal.",
                ],
            ),
            (
                "2. HS codes and valuation",
                [
                    "Each line item must carry a Harmonised System (HS) code of at least six digits. "
                    "The declared value must be the transaction value in the invoice currency. "
                    "Undervaluing goods to reduce duty is customs fraud and voids all insurance.",
                ],
            ),
            (
                "3. Duties and thresholds",
                [
                    "• Shipments with a declared value at or below 50,000 rupees may use a simplified courier declaration.",
                    "• Shipments above that threshold require a full Shipping Bill and may be assessed for GST and duty drawback.",
                    "• Gifts are not exempt from declaration; the market value must still be stated.",
                ],
            ),
        ],
    },
    "dimensional_weight_pricing.pdf": {
        "title": "Dimensional-Weight Pricing",
        "intro": "Carriers charge by whichever is greater: the actual weight of a "
        "parcel or its dimensional (volumetric) weight. This rewards dense "
        "packing and discourages oversized boxes.",
        "sections": [
            (
                "1. The formula",
                [
                    "Dimensional weight in kilograms = (length x width x height in centimetres) divided by 5000.",
                    "The chargeable weight is the greater of the actual weight and the dimensional weight, "
                    "rounded up to the next 0.5 kilogram.",
                ],
            ),
            (
                "2. Worked example",
                [
                    "A box measuring 40 by 30 by 25 centimetres has a volume of 30,000 cubic centimetres. "
                    "Divided by 5000 this gives a dimensional weight of 6 kilograms. "
                    "If the parcel actually weighs 4 kilograms, it is billed as 6 kilograms.",
                ],
            ),
            (
                "3. When it applies",
                [
                    "• The divisor of 5000 applies to domestic and international air service.",
                    "• A divisor of 4000 applies to premium same-day service.",
                    "• Ground freight below 2 kilograms is billed on actual weight only.",
                ],
            ),
        ],
    },
    "claims_and_damage_policy.pdf": {
        "title": "Claims and Damage Policy",
        "intro": "This policy explains how to file a claim for a lost or damaged "
        "shipment and the time limits that apply.",
        "sections": [
            (
                "1. Filing a claim",
                [
                    "• A claim for visible damage must be filed within 30 calendar days of the delivery date.",
                    "• A claim for loss may be filed once a shipment is 10 days past its promised delivery date.",
                    "• Claims are submitted through the online claims portal with the tracking number and proof of value.",
                ],
            ),
            (
                "2. Required evidence",
                [
                    "The claimant must provide the commercial invoice or purchase receipt, photographs of the "
                    "damaged item and its packaging, and the original packaging for inspection. "
                    "Claims without proof of value are settled at the default liability rate only.",
                ],
            ),
            (
                "3. Liability limits and settlement",
                [
                    "• Default liability is 100 rupees per kilogram unless a higher declared value was purchased.",
                    "• Settlement is paid within 15 business days of claim approval.",
                    "• Consequential losses, such as lost profit, are never covered.",
                ],
            ),
        ],
    },
    "delivery_exception_codes.pdf": {
        "title": "Delivery Exception Codes",
        "intro": "When a shipment cannot move normally, the tracking system records "
        "an exception code. This reference explains each code and the action taken.",
        "sections": [
            (
                "1. Address and recipient exceptions",
                [
                    "• DEX01 — Incorrect or incomplete address. The parcel is held pending an address correction.",
                    "• DEX07 — Customer not available. A redelivery is attempted on the next business day.",
                    "• DEX08 — Business closed. Delivery is re-attempted during business hours.",
                    "• DEX12 — Recipient refused the shipment. The parcel is returned to the shipper.",
                ],
            ),
            (
                "2. Operational exceptions",
                [
                    "• DEX21 — Weather or natural-event delay. No redelivery fee applies.",
                    "• DEX23 — Customs hold pending documentation. The shipper must supply the missing paperwork.",
                    "• DEX31 — Damaged in transit; parcel routed to the claims team.",
                ],
            ),
            (
                "3. Resolution window",
                [
                    "A shipment under an address exception is held for 5 business days. "
                    "If it is not corrected within that window, it is returned to the shipper at the shipper's cost.",
                ],
            ),
        ],
    },
    "dangerous_goods.pdf": {
        "title": "Dangerous Goods Handling",
        "intro": "Dangerous goods are items that can harm people, property, or the "
        "environment in transit. They require special declaration and handling.",
        "sections": [
            (
                "1. Classification",
                [
                    "Dangerous goods follow the nine UN hazard classes. The most common in parcels are:",
                    "• Class 3 — Flammable liquids, such as paints and solvents.",
                    "• Class 8 — Corrosives, such as certain cleaning agents.",
                    "• Class 9 — Miscellaneous, which includes lithium batteries and magnetised material.",
                ],
            ),
            (
                "2. Declaration and packaging",
                [
                    "• A Shipper's Declaration for Dangerous Goods must accompany each shipment.",
                    "• Only UN-specification packaging marked with the correct UN number may be used.",
                    "• Each package must display the correct hazard label at least 100 by 100 millimetres in size.",
                ],
            ),
            (
                "3. Air limits for lithium batteries",
                [
                    "Lithium-ion cells shipped by air must be at a state of charge of 30 percent or less. "
                    "Batteries above 100 watt-hours require full dangerous-goods approval and are not accepted on passenger aircraft.",
                ],
            ),
        ],
    },
    "service_levels_and_transit.pdf": {
        "title": "Service Levels and Transit Times",
        "intro": "This document describes the available service levels and their "
        "committed transit times for domestic India shipments.",
        "sections": [
            (
                "1. Service levels",
                [
                    "• PRIORITY — next business day by 12:00 noon between metro cities.",
                    "• EXPRESS — delivery within 2 business days nationwide.",
                    "• STANDARD — delivery within 4 to 6 business days nationwide.",
                ],
            ),
            (
                "2. Cut-off times",
                [
                    "• The pickup cut-off for same-day induction is 17:00 local time.",
                    "• Parcels tendered after the cut-off are inducted the next business day.",
                    "Transit commitments exclude Sundays and gazetted public holidays.",
                ],
            ),
            (
                "3. Money-back guarantee",
                [
                    "If a PRIORITY shipment misses its commitment for any reason other than a listed exception, "
                    "the shipper may request a refund of the service charge within 15 days of the delivery scan.",
                ],
            ),
        ],
    },
    "insurance_and_liability.pdf": {
        "title": "Insurance, Declared Value and Liability",
        "intro": "This document explains the difference between default carrier "
        "liability and optional declared-value coverage.",
        "sections": [
            (
                "1. Default liability",
                [
                    "Every shipment carries default liability of 100 rupees per kilogram of actual weight, "
                    "regardless of the goods' real value. This is not insurance; it is a capped liability.",
                ],
            ),
            (
                "2. Declared-value coverage",
                [
                    "• A shipper may declare a higher value up to a maximum of 500,000 rupees per shipment.",
                    "• The coverage fee is 20 rupees per 1,000 rupees of declared value, with a minimum fee of 50 rupees.",
                    "• Declared value must never exceed the genuine replacement cost of the goods.",
                ],
            ),
            (
                "3. Exclusions",
                [
                    "Coverage does not apply to items that were prohibited, poorly packaged, or inaccurately described. "
                    "Cash, jewellery, and antiques are excluded from declared-value coverage entirely.",
                ],
            ),
        ],
    },
    "returns_and_refused.pdf": {
        "title": "Returns and Refused Shipments",
        "intro": "This policy covers what happens when a shipment is returned, "
        "refused, or undeliverable.",
        "sections": [
            (
                "1. Refused shipments",
                [
                    "• When a recipient refuses delivery (exception DEX12), the parcel is returned to the shipper.",
                    "• The shipper is billed the return transportation at the original service rate.",
                ],
            ),
            (
                "2. Undeliverable shipments",
                [
                    "A shipment that cannot be delivered or returned within 15 business days is classed as undeliverable. "
                    "Undeliverable parcels are held at a central facility for 30 days before disposal.",
                ],
            ),
            (
                "3. Return labels",
                [
                    "• A prepaid return label is valid for 30 days from the date of issue.",
                    "• Return parcels must meet the same packaging standards as outbound shipments.",
                    "• Refunds for returned goods are issued by the merchant, not the carrier.",
                ],
            ),
        ],
    },
}


def _footer(canvas, doc) -> None:
    """Draw the synthetic-sample footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillGray(0.5)
    canvas.drawCentredString(A4[0] / 2.0, 1.2 * cm, FOOTER_TEXT)
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _build(filename: str, spec: dict, out_dir: str) -> str:
    """Render a single document spec to a PDF and return its path."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Title"], fontSize=18, spaceAfter=14
    )
    heading_style = ParagraphStyle(
        "DocHeading", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        "DocBody", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=6
    )

    path = os.path.join(out_dir, filename)
    pdf = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
        title=spec["title"],
    )

    story: list = [Paragraph(spec["title"], title_style),
                   Paragraph(spec["intro"], body_style),
                   Spacer(1, 0.3 * cm)]

    for heading, lines in spec["sections"]:
        story.append(Paragraph(heading, heading_style))
        bullets: list = []
        for line in lines:
            if line.startswith("• "):
                bullets.append(ListItem(Paragraph(line[2:], body_style), leftIndent=10))
            else:
                if bullets:
                    story.append(ListFlowable(bullets, bulletType="bullet", start="•"))
                    bullets = []
                story.append(Paragraph(line, body_style))
        if bullets:
            story.append(ListFlowable(bullets, bulletType="bullet", start="•"))

    pdf.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path


def main() -> None:
    settings = get_settings()
    out_dir = settings.docs_dir
    os.makedirs(out_dir, exist_ok=True)

    written = [_build(name, spec, out_dir) for name, spec in DOCS.items()]
    print(f"Wrote {len(written)} synthetic documents to {out_dir}/")
    for p in written:
        print(f"  - {os.path.basename(p)}")


if __name__ == "__main__":
    main()
