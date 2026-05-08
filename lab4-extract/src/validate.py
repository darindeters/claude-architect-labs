"""
Semantic validators (Step 5).

These run AFTER tool_use produces a syntactically-valid Invoice. They
catch the kind of error the schema can't: line items that don't sum to
the stated total, mutually inconsistent fields, calculated vs stated
discrepancies.
"""
from .schema import Invoice


def validate_totals_match(inv: Invoice) -> str | None:
    """Return an error message if line items don't reconcile with the stated total.

    Returns None when everything checks out (or when there's not enough
    data to check, which is also fine — that's a job for human review,
    not for this validator to flag.)
    """
    # TODO (step 5): if inv.line_items is non-empty and inv.stated_total
    # is not None, sum the line item amounts (skip None) and compare to
    # stated_total + (stated_tax or 0). If the difference exceeds a small
    # epsilon (say, $0.05), return a description.
    return None
