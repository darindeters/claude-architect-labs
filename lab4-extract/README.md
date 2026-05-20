# Lab 4 — Structured extraction with validation and batch

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 4.
Pydantic schema, single-doc extraction via `tool_use`, semantic validators,
and a Message Batches placeholder. Ten sample invoices including deliberate
edge cases.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 4 — seven recipes; each one maps to a TODO in this scaffold.)

> **First time running these labs?** Read the [pitfalls section in the root
> README](../README.md#read-this-first--five-things-that-will-save-you-20-minutes)
> first — Python version, single-shot invocation, and "what TODO stubs do by default."

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- ~$5 budget

## Setup

```bash
cd lab4-extract
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # then edit .env and add your key
```

## First run — confirm extraction works

```bash
python -m src.extract fixtures/invoice_001.txt
```

Expected output:

```
--- extracted ---
{
  "vendor_name": "ACME LIGHTING CO.",
  "vendor_address": "123 Industrial Way, Portland, OR 97201",
  "invoice_number": "INV-2026-0142",
  "issue_date": "2026-04-15",
  "due_date": "2026-05-15",
  "line_items": [
    {
      "description": "LED Panel 24x24 (Daylight)",
      "quantity": 8.0,
      "unit_price": 145.00,
      "amount": 1160.00
    },
    ...
  ],
  "stated_subtotal": 1640.00,
  "stated_tax": 147.60,
  "stated_total": 1787.60,
  "calculated_total": 1787.60,
  "expense_category": "other",
  "expense_category_detail": "lighting fixtures",
  "conflict_detected": false,
  "conflict_details": null,
  "notes": null
}

--- semantic validation ---
OK
```

The exact values will reflect what's in the fixture file. Two things to confirm:

1. **No `null` fields where the source has clear values** — vendor name, dates, line items,
   totals should all be populated. `stated_total` and `calculated_total` should both be
   present (the model is asked to compute them independently — recipe 5 makes them disagree).
2. **`semantic validation` prints `OK`** — but only because `validate_totals_match` is
   a TODO stub returning `None`. Recipe 5 implements it; until then every fixture validates
   as OK regardless of its math.

**If you see something else:**

- *`anthropic.AuthenticationError`* → API key not in env. Check `echo $ANTHROPIC_API_KEY`.
- *`pydantic_core._pydantic_core.ValidationError`* → The model returned something that
  doesn't match the Pydantic schema. Pre-recipe-3 this raises; recipe 3 wraps it in the
  retry loop.
- *`RuntimeError: model did not call the extraction tool`* → `tool_choice` isn't forcing
  `record_invoice`. Inspect `src/extract.py`'s `extract()` function.
- *`TypeError: unsupported operand type(s) for |`* → Python 3.9. Make a fresh venv with 3.10+.

## The planted edge cases

The fixtures directory contains ten invoices with deliberate problems:

| File | Problem to catch | What you should see |
|---|---|---|
| `invoice_001.txt`–`invoice_005.txt` | Clean — should extract cleanly | All fields populated, `OK` validation |
| `invoice_006_missing.txt` | Missing required-looking fields (test nullable behavior) | `vendor_name: null` with default schema. Flip to required and watch fabrication. |
| `invoice_007_bad_total.txt` | Line items don't sum to stated total (test semantic validator) | Extraction succeeds; recipe 5's validator catches `stated_total` ≠ `calculated_total` |
| `invoice_008_informal_date.txt` | Informal date format (test format normalization) | Pre-recipe-3: may come back wrong-typed. Recipe 3's retry loop fixes it. |
| `invoice_009_other_category.txt` | Category outside the enum (test "other" + detail pattern) | `expense_category: "other"` with `expense_category_detail` populated |
| `invoice_010_conflict.txt` | Two conflicting amounts in source (test conflict_detected flag) | Model sets `conflict_detected: true` and explains in `notes` |

## Recipes → files

| Recipe | What you do | Where you work |
|---|---|---|
| **1 — Define the extraction tool** | Read `schema.py`. Note `Optional` defaults, the `expense_category` enum with `'other'`+`detail` pairing, and the `unclear` escape hatch. The `INVOICE_TOOL_SCHEMA` is what gets passed to the API. | `src/schema.py` (already done — read carefully) |
| **2 — Process absent fields** | Run `invoice_006_missing.txt`; confirm missing fields return null. Then flip one field to required (remove its `Optional`), regenerate the schema, re-run, and watch the model fabricate. Revert. | `src/schema.py` — flip one `Optional` |
| **3 — Validation-retry loop** | Implement `retry_with_feedback` so a Pydantic `ValidationError` triggers a second call that includes the document, the failed extraction, and the specific error. Track which error classes recover vs. don't. | `src/extract.py` — `retry_with_feedback` |
| **4 — Few-shot examples** | The scaffold's `FEW_SHOT_EXAMPLES` block is filled in with the canonical three (informal date, missing required-looking field, conflicting totals). Add 1-2 more targeting your failure formats; measure empty-field rate before and after. | `src/extract.py` — `FEW_SHOT_EXAMPLES` |
| **5 — Self-correction validators** | Implement `validate_totals_match`. The schema has both `stated_total` (verbatim from doc) and `calculated_total` (model sums independently). When they disagree by more than $0.05, flag the discrepancy. | `src/validate.py` — `validate_totals_match` |
| **6 — Batch processing** | Implement `submit_batch`, `poll_until_done`, `collect_results`. Use deterministic `custom_id` (e.g., the filename) so failures can be resubmitted by ID. Document the SLA math: 24h batch ceiling + buffer for failure handling = your customer SLA. | `src/batch.py` (placeholders for all three) |
| **7 — Confidence calibration** | Extend the schema with paired `{field}_confidence: float` for the meaningful fields. Hand-label 20-30 documents as ground truth. Calibrate the threshold by walking confidence cutoffs 0.1→0.9. Stratify accuracy by document type AND field; look for hidden weak segments. | `src/schema.py` (new fields), plus a `tools/calibrate.py` you write |

## Naming notes (guide vs scaffold)

| Guide pseudocode | Scaffold reality |
|---|---|
| `payment_terms` enum + `payment_terms_detail` | `expense_category` enum + `expense_category_detail` (same `'other' + detail` pattern, different domain choice; the lesson is the pairing) |
| `stated_total` + `calculated_total` returned by the model | Same names; the scaffold's schema exposes both fields (the validator compares them) |
| `error(category, ...)` helper | Lab 1's helper; not directly used in Lab 4 — extraction failures surface as Pydantic `ValidationError` and trigger the retry loop |

The walkthrough uses `payment_terms` as the running example for the
`'other' + detail` pattern; this scaffold uses `expense_category`. They're
the same pattern applied to a different invoice field — pick whichever you
prefer if you extend the schema. The lesson (enum + open-ended escape hatch
+ explicit detail field) is identical.

## What you should see per recipe

### Recipe 2 — Required vs nullable (the fabrication demo)

**Default — `vendor_name: Optional[str] = None`:**

```bash
python -m src.extract fixtures/invoice_006_missing.txt
```

Expected: `vendor_name: null` in the output. The fixture is a coffee-shop receipt with no
vendor letterhead, so the model correctly admits it can't fill the field.

**Now flip `vendor_name` to required** in `src/schema.py`:

```python
class Invoice(BaseModel):
    vendor_name: str                       # was: Optional[str] = Field(default=None, ...)
    ...
```

Re-run the same fixture:

```bash
python -m src.extract fixtures/invoice_006_missing.txt
```

Expected: `vendor_name` now contains a **fabricated value** — usually something plausible
like `"Coffee Shop"` or `"Unknown Coffee Vendor"`. The model invented a value to satisfy
the schema. No "I don't know" indicator anywhere.

This is *the* lesson. Revert to `Optional[str] = Field(default=None, ...)` when done —
required fields should be exceptions, not defaults.

### Recipe 3 — Validation-retry loop (implement the stub)

Before implementation, `retry_with_feedback` raises `NotImplementedError`. Test fixtures
with format issues just propagate the Pydantic `ValidationError`.

**Implement** `retry_with_feedback`:

```python
def retry_with_feedback(document_text: str, failed: Invoice, error_message: str) -> Invoice:
    messages = [
        {"role": "user", "content": document_text},
        {"role": "assistant", "content": (
            f"Previous extraction attempt:\n{failed.model_dump_json(indent=2)}\n\n"
            f"That extraction failed validation: {error_message}"
        )},
        {"role": "user", "content": (
            "Re-extract using the schema correctly. "
            "Use null for genuinely-absent fields; do not fabricate values."
        )},
    ]
    response = client.messages.create(
        model=MODEL, max_tokens=2048, system=SYSTEM,
        tools=[INVOICE_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "record_invoice"},
        messages=messages,
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "record_invoice":
            return Invoice.model_validate(block.input)
    raise RuntimeError("retry did not produce a tool call")
```

Then wrap your top-level `extract()` call in a loop that catches `ValidationError` and
calls `retry_with_feedback`. Cap at 2 attempts; the model rarely recovers on attempt 3.

Test on `invoice_008_informal_date.txt` — you should see the retry kick in on roughly half
of runs, succeeding on attempt 2 with a properly-formatted ISO date.

### Recipe 5 — Semantic validator (implement the stub)

The schema asks the model for both `stated_total` (verbatim from the document) and
`calculated_total` (computed independently from line items). Before implementing the
validator, every fixture prints `OK` regardless of whether the two agree:

```bash
python -m src.extract fixtures/invoice_007_bad_total.txt

# --- semantic validation ---
# OK         ← but the totals don't actually match!
```

**Implement** `validate_totals_match` in `src/validate.py`:

```python
EPSILON = 0.05

def validate_totals_match(inv: Invoice) -> str | None:
    if inv.stated_total is None or inv.calculated_total is None:
        return None   # not enough data to check
    diff = inv.stated_total - inv.calculated_total
    if abs(diff) > EPSILON:
        return (f"stated_total={inv.stated_total:.2f} differs from "
                f"calculated_total={inv.calculated_total:.2f} (diff={diff:+.2f})")
    return None
```

Re-run the bad-total fixture:

```bash
python -m src.extract fixtures/invoice_007_bad_total.txt

# --- semantic validation ---
# FLAG: stated_total=185.50 differs from calculated_total=175.50 (diff=+10.00)
```

The `FLAG:` line is your routing signal — in a production pipeline, this row goes to a
"needs human review" queue instead of the happy-path output bucket. The validator runs in
Python, not in the model's head; that's why it's deterministic. The model can hallucinate
one number; it has a hard time hallucinating both consistently.

Test on a clean fixture to confirm no false positives:

```bash
python -m src.extract fixtures/invoice_001.txt

# --- semantic validation ---
# OK
```

### Recipe 6 — Batch processing (all TODO stubs)

Don't open `src/batch.py` until `extract.py` runs reliably on at least 5 fixtures. The
Message Batches API has no multi-turn tool calling, so all the work from recipes 1–5 must
be solid before you batch anything. The stubbed functions will tell you which step to do
when you call them:

```bash
python -c "from src.batch import submit_batch; submit_batch({})"
# NotImplementedError: step 6 of the lab
```

When implemented, expected behavior:
- `submit_batch({custom_id: text})` returns a batch ID immediately
- `poll_until_done(batch_id)` blocks for up to 24 hours (poll every 60s)
- `collect_results(batch_id)` returns `{custom_id: Invoice_or_error_dict}`

## What success looks like

- Clean invoices extract cleanly on at least 8/10.
- `invoice_006_missing.txt` returns `null` for the missing fields rather
  than fabricating. Flip one of those fields to required and the model
  starts inventing — that side-by-side is the lesson.
- `invoice_007_bad_total.txt` is caught by `validate_totals_match`:
  `stated_total` and `calculated_total` disagree, the validator flags it,
  and the document routes to a "needs review" bucket rather than the happy path.
- The retry loop visibly resolves a format error (e.g., `"03/14/26"` → ISO)
  on the second try; the same loop visibly fails to resolve when the source
  is genuinely missing required information.
- Stratified accuracy reveals at least one segment performing measurably
  worse than the headline number. If everything is uniformly excellent,
  your validation set lacks variety.

See the full walkthrough at <https://learn.techwithdarin.com/certs/claude-architect/#lab>.
