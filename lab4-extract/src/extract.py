"""
Single-document extraction via tool_use.

tool_choice forces the model to call our extraction tool, eliminating
the "free-form JSON in text" failure mode.

Run:
    python -m src.extract fixtures/invoice_001.txt
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .schema import Invoice, INVOICE_TOOL_SCHEMA
from .validate import validate_totals_match


load_dotenv()
client = Anthropic()
MODEL = "claude-sonnet-4-5"


# Step 4: Few-shot examples for ambiguous cases. Show, don't tell.
FEW_SHOT_EXAMPLES = """\
Example 1 — informal date:
  Source: "Date: 03/14/26"
  Output: issue_date = "2026-03-14"

Example 2 — missing required-looking field:
  Source: invoice with no vendor letterhead and no signature line
  Output: vendor_name = null  (do NOT guess from the recipient address)

Example 3 — conflicting totals:
  Source: line items sum to $1,250.00 but "Total: $1,500.00" appears at bottom
  Output: stated_total = 1500.00, conflict_detected = true,
          notes = "line items sum to 1250.00 but stated total is 1500.00"
"""


SYSTEM = (
    "You extract structured data from invoices. Use null for fields not present "
    "in the source. Do NOT fabricate values to satisfy a schema field. "
    "Compute stated_total (verbatim) and calculated_total (sum of line items, "
    "computed by you INDEPENDENTLY) — these MUST be computed separately even if "
    "they happen to match. If the source has internally contradictory amounts, "
    "set conflict_detected=true and populate conflict_details with the two "
    "values and the difference.\n\n"
    + FEW_SHOT_EXAMPLES
)


def extract(document_text: str) -> Invoice:
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM,
        tools=[INVOICE_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "record_invoice"},
        messages=[{"role": "user", "content": document_text}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "record_invoice":
            return Invoice.model_validate(block.input)
    raise RuntimeError("model did not call the extraction tool")


def retry_with_feedback(document_text: str, failed: Invoice, error_message: str) -> Invoice:
    """Step 3: re-prompt with the document + failed extraction + specific error."""
    # TODO (step 3): implement. Send a second messages.create with:
    #   - the original document
    #   - the failed extraction (failed.model_dump_json())
    #   - the specific validation error
    # then return the corrected Invoice.
    raise NotImplementedError("step 3 of the lab")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.extract <path-to-invoice.txt>")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    path = Path(sys.argv[1])
    text = path.read_text()
    invoice = extract(text)
    print("--- extracted ---")
    print(invoice.model_dump_json(indent=2))

    print("\n--- semantic validation ---")
    issue = validate_totals_match(invoice)
    if issue:
        print(f"FLAG: {issue}")
    else:
        print("OK")


if __name__ == "__main__":
    main()
