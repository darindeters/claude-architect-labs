"""
Semantic validators (Step 5).

These run AFTER tool_use produces a syntactically-valid Invoice. They
catch the kind of error the schema can't: line items that don't sum to
the stated total, mutually inconsistent fields, calculated vs stated
discrepancies.
"""
from .schema import Invoice


EPSILON = 0.05   # cents-level tolerance for floating-point and rounding


def validate_totals_match(inv: Invoice) -> str | None:
    """Return an error message if the two totals disagree.

    The walkthrough's recipe 5 pattern: the model produces stated_total AND
    calculated_total INDEPENDENTLY. This validator runs in Python (not in the
    model's head) and compares them. The deterministic comparison is the
    whole point — semantic validation lives in code, not in a prompt.

    Returns None when:
      - both totals are within EPSILON of each other, OR
      - there isn't enough data to check (one or both are None).
    Sets inv.conflict_detected = True and inv.conflict_details when they
    disagree by more than EPSILON, so downstream routing sees the flag.
    """
    # TODO (recipe 5): if both stated_total and calculated_total are present,
    # compare them. If the absolute diff exceeds EPSILON, set
    # inv.conflict_detected = True, populate inv.conflict_details with the
    # two values and the signed diff, and return the description string.
    # If only stated_total is present, fall back to summing line_items[].amount
    # in code and comparing to stated_total + (stated_tax or 0).
    return None
