# Lab 4 — Structured extraction with validation and batch

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 4.
Pydantic schema, single-doc extraction via `tool_use`, semantic validators,
and a Message Batches placeholder. Ten sample invoices including deliberate
edge cases.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 4 — seven recipes; each one maps to a TODO in this scaffold.)

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

## Recipes → files

| Recipe | What you do | Where you work |
|---|---|---|
| **1 — Define the extraction tool** | Read `schema.py`. Note `Optional` defaults, the `expense_category` enum with `'other'`+`detail` pairing, and the `unclear` escape hatch. The `INVOICE_TOOL_SCHEMA` is what gets passed to the API. | `src/schema.py` (already done — read carefully) |
| **2 — Process absent fields** | Run `invoice_006_missing.txt`; confirm missing fields return null. Then flip one field to required (remove its `Optional`), regenerate the schema, re-run, and watch the model fabricate. Revert. | `src/schema.py` — flip one `Optional` |
| **3 — Validation-retry loop** | Implement `retry_with_feedback` so a Pydantic `ValidationError` triggers a second call that includes the document, the failed extraction, and the specific error. Track which error classes recover vs. don't. | `src/extract.py` — `retry_with_feedback` |
| **4 — Few-shot examples** | The scaffold's `FEW_SHOT_EXAMPLES` block is filled in with the canonical three (informal date, missing required-looking field, conflicting totals). Add 1-2 more targeting your failure formats; measure empty-field rate before and after. | `src/extract.py` — `FEW_SHOT_EXAMPLES` |
| **5 — Self-correction validators** | Implement `validate_totals_match`. The schema now has both `stated_total` (verbatim from doc) and `calculated_total` (model sums independently). When they disagree by more than $0.05, flip `conflict_detected = True` and populate `conflict_details`. | `src/validate.py` — `validate_totals_match` |
| **6 — Batch processing** | Implement `submit_batch`, `poll_until_done`, `collect_results`. Use deterministic `custom_id` (e.g., the filename) so failures can be resubmitted by ID. Document the SLA math: 24h batch ceiling + buffer for failure handling = your customer SLA. | `src/batch.py` (placeholders for all three) |
| **7 — Confidence calibration** | Extend the schema with paired `{field}_confidence: float` for the meaningful fields. Hand-label 20-30 documents as ground truth. Calibrate the threshold by walking confidence cutoffs 0.1→0.9. Stratify accuracy by document type AND field; look for hidden weak segments. | `src/schema.py` (new fields), plus a `tools/calibrate.py` you write |

## Naming notes (guide vs scaffold)

| Guide pseudocode | Scaffold reality |
|---|---|
| `payment_terms` enum + `payment_terms_detail` | `expense_category` enum + `expense_category_detail` (same `'other' + detail` pattern, different domain choice; the lesson is the pairing) |
| `stated_total` + `calculated_total` returned by the model | Same names; the scaffold's schema now exposes both fields (the validator compares them) |
| `error(category, ...)` helper | Lab 1's helper; not directly used in Lab 4 — extraction failures surface as Pydantic `ValidationError` and trigger the retry loop |

The walkthrough uses `payment_terms` as the running example for the
`'other' + detail` pattern; this scaffold uses `expense_category`. They're
the same pattern applied to a different invoice field — pick whichever you
prefer if you extend the schema. The lesson (enum + open-ended escape hatch
+ explicit detail field) is identical.

## What success looks like

- Clean invoices extract cleanly on at least 8/10.
- `invoice_006_missing.txt` returns `null` for the missing fields rather
  than fabricating. Flip one of those fields to required and the model
  starts inventing — that side-by-side is the lesson.
- `invoice_007_bad_total.txt` is caught by `validate_totals_match`:
  `conflict_detected = True`, `conflict_details` names the two values, and
  the document routes to a "needs review" bucket rather than the happy path.
- The retry loop visibly resolves a format error (e.g., `"03/14/26"` → ISO)
  on the second try; the same loop visibly fails to resolve when the source
  is genuinely missing required information.
- Stratified accuracy reveals at least one segment performing measurably
  worse than the headline number. If everything is uniformly excellent,
  your validation set lacks variety.

See the full walkthrough at <https://learn.techwithdarin.com/certs/claude-architect/#lab>.
