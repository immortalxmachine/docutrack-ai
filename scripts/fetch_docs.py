"""
Download the real, public-domain document corpus.

Every document fetched here is a work of the U.S. federal government and is in
the public domain (17 U.S.C. § 105). No copyrighted carrier policies or
paywalled material is used. See ``data/docs/SOURCES.md`` for the full table of
titles, issuers and licensing.

Run:
    python -m scripts.fetch_docs
Output:
    data/docs/*.pdf   (10 documents)

Each download is validated to be a real PDF (``%PDF`` magic bytes) before it is
kept; a failed or non-PDF response is reported and skipped rather than written.
"""
from __future__ import annotations

import os

import requests

from app.config import get_settings

# filename -> official source URL (see data/docs/SOURCES.md for titles/licensing)
DOCS: dict[str, str] = {
    "cbp_importing_into_us.pdf":
        "https://www.cbp.gov/sites/default/files/documents/Importing%20into%20the%20U.S.pdf",
    "cbp_reasonable_care.pdf":
        "https://www.cbp.gov/sites/default/files/assets/documents/2020-Feb/icprescare2017revision.pdf",
    "cbp_icp_rulings_program.pdf":
        "https://www.cbp.gov/sites/default/files/assets/documents/2023-Sep/"
        "ICP-CBP-Rulings-Program-20%20Sept%202023-PBRB%20approved%20aak%20FINAL.pdf",
    "cbp_icp_apparel_marking.pdf":
        "https://cbp.gov/sites/default/files/assets/documents/2020-Feb/"
        "ICP-Marking-for-Wearing-Apparel-2008-Final.pdf",
    "cbp_icp_country_of_origin_marking.pdf":
        "https://www.ams.usda.gov/sites/default/files/media/CBP%20Markings%20Document%20on%20Imports.pdf",
    "cbp_ecommerce_guide.pdf":
        "https://www.cbp.gov/sites/default/files/assets/documents/2020-Jan/"
        "E-Commerce%20Compliance%20Guide%20for%20Online%20Sellers.pdf",
    "census_current_ftr.pdf":
        "https://www.census.gov/foreign-trade/regulations/regs/Current_FTR.pdf",
    "census_export_quickguide.pdf":
        "https://www2.census.gov/programs-surveys/trade/regulations/quickguide.pdf",
    "cfr_title49_hazmat_general.pdf":
        "https://www.govinfo.gov/content/pkg/CFR-2023-title49-vol2/pdf/CFR-2023-title49-vol2-part171.pdf",
    "cfr_title19_marking_part134.pdf":
        "https://www.govinfo.gov/content/pkg/CFR-2018-title19-vol1/pdf/CFR-2018-title19-vol1-part134.pdf",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}


def _fetch_one(url: str, dest: str) -> bool:
    """Download one PDF, returning True only if a valid PDF was written."""
    resp = requests.get(url, headers=_HEADERS, timeout=120, allow_redirects=True)
    if resp.status_code != 200:
        print(f"  ! HTTP {resp.status_code} — skipped")
        return False
    if not resp.content.startswith(b"%PDF"):
        print(f"  ! response is not a PDF ({len(resp.content)} bytes) — skipped")
        return False
    with open(dest, "wb") as fh:
        fh.write(resp.content)
    print(f"  -> {len(resp.content):,} bytes")
    return True


def main() -> None:
    out_dir = get_settings().docs_dir
    os.makedirs(out_dir, exist_ok=True)

    ok = 0
    for name, url in DOCS.items():
        print(f"{name}")
        if _fetch_one(url, os.path.join(out_dir, name)):
            ok += 1
    print(f"\nFetched {ok}/{len(DOCS)} documents into {out_dir}/")
    if ok < len(DOCS):
        print("Some downloads failed (an agency may have moved a file). "
              "Check data/docs/SOURCES.md and update the URL.")


if __name__ == "__main__":
    main()
