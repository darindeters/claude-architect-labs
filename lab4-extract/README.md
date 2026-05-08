# Lab 4 — Structured extraction with validation and batch

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 4.
Pydantic schema, single-doc extraction via `tool_use`, semantic validators,
and a Message Batches placeholder. Ten sample invoices including
deliberate edge cases.

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)
- ~$5 budget

## Setup

```bash
cd lab4-extract
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run a single document

```bash
python -m src.extract fixtures/invoice_001.txt
```

## The planted edge cases

The fixtures directory contains ten invoices with deliberate problems:

| File | Problem to catch |
|---|---|
| `invoice_001.txt`–`invoice_005.txt` | Clean — should extract cleanly |
| `invoice_006_missing.txt` | Missing required-looking fields (test nullable behavior) |
| `invoice_007_bad_total.txt` | Line items don't sum to stated total (test semantic validator) |
| `invoice_008_informal_date.txt` | Informal date format (test format normalization) |
| `invoice_009_other_category.txt` | Category outside the enum (test "other" + detail pattern) |
| `invoice_010_conflict.txt` | Two conflicting amounts in source (test conflict_detected flag) |

## Lab steps mapped to files

| Step | Where you work |
|---|---|
| 1 — Define extraction tool | `src/schema.py` is filled in. Read carefully. |
| 2 — Required vs nullable | `src/schema.py` — flip a field to required, watch fabrication. |
| 3 — Validation-retry loop | `src/extract.py` — implement `retry_with_feedback` |
| 4 — Few-shot examples | `src/extract.py` — fill in `FEW_SHOT_EXAMPLES` |
| 5 — Self-correction validator | `src/validate.py` — implement `validate_totals_match` |
| 6 — Batch processing | `src/batch.py` — only after `extract.py` is reliable on 5 docs |
| 7 — Confidence calibration | `src/extract.py` — add `field_confidence` to schema |

## What success looks like

- Clean invoices extract cleanly on at least 8/10
- `invoice_006_missing.txt` returns `null` for the missing fields rather than fabricating values
- `invoice_007_bad_total.txt` is caught by `validate_totals_match` and routed to the conflict path
- The retry loop visibly resolves a format error (e.g., `"03/14/26"` → ISO) but visibly fails when info is genuinely absent
