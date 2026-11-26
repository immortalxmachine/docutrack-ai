# Document corpus — sources & licensing

Every document in this folder is a **work of the U.S. federal government** and is
therefore in the **public domain** in the United States (17 U.S.C. § 105 — works
prepared by U.S. government officers/employees as part of their official duties
are not subject to copyright). No copyrighted carrier policies, IATA material, or
other paywalled content is used.

These are **real, published** shipping / customs / logistics documents — not
synthetic samples. They were downloaded from the official agency sites listed
below. Re-download them any time with `python -m scripts.fetch_docs`.

| File | Title | Issuer | Pages | Source URL |
|------|-------|--------|------:|------------|
| `cbp_importing_into_us.pdf` | Importing into the United States — A Guide for Commercial Importers | U.S. Customs and Border Protection (CBP) | 211 | https://www.cbp.gov/sites/default/files/documents/Importing%20into%20the%20U.S.pdf |
| `cbp_reasonable_care.pdf` | Reasonable Care — An Informed Compliance Publication | CBP | 19 | https://www.cbp.gov/sites/default/files/assets/documents/2020-Feb/icprescare2017revision.pdf |
| `cbp_icp_rulings_program.pdf` | U.S. Customs and Border Protection Rulings Program — Informed Compliance Publication | CBP | 44 | https://www.cbp.gov/sites/default/files/assets/documents/2023-Sep/ICP-CBP-Rulings-Program-20%20Sept%202023-PBRB%20approved%20aak%20FINAL.pdf |
| `cbp_icp_apparel_marking.pdf` | Marking Requirements for Wearing Apparel — Informed Compliance Publication | CBP | 16 | https://cbp.gov/sites/default/files/assets/documents/2020-Feb/ICP-Marking-for-Wearing-Apparel-2008-Final.pdf |
| `cbp_icp_country_of_origin_marking.pdf` | Marking of Country of Origin on U.S. Imports — Acceptable Terminology and Methods for Marking | CBP (mirrored on ams.usda.gov) | 10 | https://www.ams.usda.gov/sites/default/files/media/CBP%20Markings%20Document%20on%20Imports.pdf |
| `cbp_ecommerce_guide.pdf` | E-Commerce Elements of Compliance — How to Get Your Package Cleared and Delivered on Time | CBP | 1 | https://www.cbp.gov/sites/default/files/assets/documents/2020-Jan/E-Commerce%20Compliance%20Guide%20for%20Online%20Sellers.pdf |
| `census_current_ftr.pdf` | Foreign Trade Regulations (15 CFR Part 30), revised Mar 30 2026 | U.S. Census Bureau | 64 | https://www.census.gov/foreign-trade/regulations/regs/Current_FTR.pdf |
| `census_export_quickguide.pdf` | Automated Export System (AES) — Quick Reference Guide | U.S. Census Bureau | 15 | https://www2.census.gov/programs-surveys/trade/regulations/quickguide.pdf |
| `cfr_title49_hazmat_general.pdf` | 49 CFR Part 171 — Hazardous Materials Regulations: General Information, Regulations, and Definitions (2023 ed.) | Office of the Federal Register / GovInfo (GPO) | 52 | https://www.govinfo.gov/content/pkg/CFR-2023-title49-vol2/pdf/CFR-2023-title49-vol2-part171.pdf |
| `cfr_title19_marking_part134.pdf` | 19 CFR Part 134 — Country of Origin Marking (2018 ed.) | Office of the Federal Register / GovInfo (GPO) | 16 | https://www.govinfo.gov/content/pkg/CFR-2018-title19-vol1/pdf/CFR-2018-title19-vol1-part134.pdf |

Downloaded 2026-11-26. If an agency later moves a file, update the URL in
`scripts/fetch_docs.py` and this table.

## Why these

They span the real document types a shipping/customs assistant is asked about:
importing procedure, informed-compliance guidance, binding rulings, country-of-origin
marking (guide, apparel-specific, and the underlying CFR), e-commerce clearance,
export filing (FTR + AES), and hazardous-materials regulation. The overlap between
the three "marking" documents is deliberate — it makes the retrieval evaluation
non-trivial (the retriever has to pick the *right* marking document).
