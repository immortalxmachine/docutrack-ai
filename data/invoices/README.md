# Sample invoices — what these are

The PDFs in this folder are **clearly-labelled SAMPLE commercial invoices** used
to demonstrate the `/extract-invoice` endpoint and the `/invoices/summary` SQL
aggregates. They are **not** real company documents and are **not** made to look
like any real importer's or exporter's paperwork:

- Every party is an obvious fictitious placeholder — `Sample Exporter N
  (fictitious)`, `Demo Importer X (fictitious)` — at `Demo Street` / `Example
  Ave` addresses.
- Each page carries a red **"SAMPLE — fictitious data, demo use only"** banner
  and footer.
- The invoice *structure* (shipper, consignee, HS-coded line items, declared
  value) is realistic so the extraction and aggregation code is genuinely
  exercised; only the *data* is fictitious.

HS codes, product descriptions, and destination countries are drawn from public
classification examples so the summary aggregates (declared value by country,
top HS codes) are non-trivial.

Regenerate with:

```bash
python -m scripts.generate_invoices
```

Why not a real third-party invoice dataset? Public commercial-invoice datasets
either contain real companies' data (a privacy/representation concern) or are
licensed images of forms rather than extractable PDFs. A small set of openly
fictitious, clearly-labelled samples is the honest way to demo the extraction
path without fabricating a real-looking company's invoice.
