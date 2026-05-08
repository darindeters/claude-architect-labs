"""
Pydantic schema for invoice extraction.

Domain 4 lessons baked into this file:

1. Default fields to OPTIONAL (nullable). Required fields tell the model to
   fabricate values to satisfy the schema. Step 2 of the lab demonstrates
   this by flipping `vendor_name` to required and watching fabrication.

2. Use enum + 'other' + detail-string for extensible categorization.
   `expense_category` shows the pattern.

3. Add an 'unclear' enum value for ambiguous cases. The model uses it
   instead of guessing.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    travel = "travel"
    software = "software"
    contractor_services = "contractor_services"
    office_supplies = "office_supplies"
    marketing = "marketing"
    other = "other"
    unclear = "unclear"


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class Invoice(BaseModel):
    # Vendor / origin
    vendor_name: Optional[str] = Field(default=None, description="Company or individual issuing the invoice")
    vendor_address: Optional[str] = None

    # Document identifiers
    invoice_number: Optional[str] = None
    issue_date: Optional[str] = Field(default=None, description="ISO 8601 date if extractable; null if absent or ambiguous")
    due_date: Optional[str] = None

    # Money
    line_items: list[LineItem] = Field(default_factory=list)
    stated_subtotal: Optional[float] = None
    stated_tax: Optional[float] = None
    stated_total: Optional[float] = Field(default=None, description="Total as stated on the document — do NOT recompute")

    # Categorization
    expense_category: ExpenseCategory = Field(default=ExpenseCategory.unclear)
    expense_category_detail: Optional[str] = Field(
        default=None,
        description="If expense_category is 'other', describe in 1-5 words. Null otherwise.",
    )

    # Self-correction signals
    conflict_detected: bool = Field(default=False, description="True if the source contains internally contradictory values")
    notes: Optional[str] = None


# JSON Schema for tool_use — pydantic gives us this for free.
INVOICE_TOOL_SCHEMA = {
    "name": "record_invoice",
    "description": (
        "Records an extracted invoice. Use null for fields that are absent or "
        "ambiguous in the source. Do NOT fabricate values to fill required-looking "
        "fields. If the source contains contradictory amounts, set conflict_detected=true "
        "and explain in notes."
    ),
    "input_schema": Invoice.model_json_schema(),
}
