"""
Four MCP-style tools for the customer support agent.

Step 2 of the lab: replace each TODO description below with a *good* one
(input format, example queries, edge cases, when to use vs alternatives).
Then run a few queries and watch tool selection improve.

Step 5 of the lab: every error path returns a structured response with
errorCategory, isRetryable, and a human-readable message — the model
uses these to decide whether to retry, escalate, or explain to the user.
"""
import json
import random
import time
from pathlib import Path
from typing import Any

FIXTURES = json.loads((Path(__file__).parent.parent / "fixtures" / "customers.json").read_text())


# ---------------------------------------------------------------------------
# Tool schemas
#
# These are deliberately weak descriptions. Step 2 of the lab is to expand
# each of them into something a model can actually route on.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_customer",
        # TODO (recipe 2): weak description — expand with input format, example
        # queries, edge cases, and explicit "use this when / do NOT use this when".
        # Reference shape from the walkthrough:
        #   "Verify a customer's identity. Input: name (string) or email (string)
        #    — provide at least one. Use BEFORE any order operation. Use when the
        #    user gives their name, email, or order context. Do NOT use to look
        #    up orders directly (use lookup_order). Returns the customer record
        #    or a structured 'no match' / 'ambiguous' result."
        "description": "Retrieves customer information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
        },
    },
    {
        "name": "lookup_order",
        # TODO (step 2): weak description.
        "description": "Retrieves order details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "process_refund",
        # TODO (step 2): weak description.
        "description": "Processes a refund.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "customer_id": {"type": "string"},
            },
            "required": ["order_id", "amount", "customer_id"],
        },
    },
    {
        "name": "escalate_to_human",
        # TODO (step 2): weak description.
        "description": "Escalates the case to a human agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "summary": {"type": "string"},
                "recommended_action": {"type": "string"},
            },
            "required": ["summary"],
        },
    },
]


# ---------------------------------------------------------------------------
# Structured error helper (recipe 5 in the guide)
# ---------------------------------------------------------------------------

def error_response(category: str, retryable: bool, message: str) -> dict[str, Any]:
    """Return a structured tool error the agent can reason about.

    category: 'transient' | 'validation' | 'business' | 'permission'
      - transient   → upstream timeout, rate limit, retryable
      - validation  → bad input, not retryable, model needs to reformulate
      - business    → policy says no (refund window expired); same as the
                      walkthrough's 'business_rule' category
      - permission  → auth / authorization failure (similar to guide's 'auth')

    The agent's tool descriptions tell it the contract:
      isRetryable=True  → retry the same call (up to 2 attempts)
      isRetryable=False → do NOT retry; explain to the user.
    """
    return {
        "isError": True,
        "errorCategory": category,
        "isRetryable": retryable,
        "message": message,
    }


# Alias for the walkthrough's preferred name. The guide writes `error(...)`;
# the scaffold uses `error_response(...)`. Both work; kwargs work in either.
error = error_response


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _maybe_chaos():
    """Uncomment to inject a 30% transient failure on every tool call.

    Step 5 of the lab: with this on, you should see retry behavior; with
    business-rule errors (refund window expired, auto_approve_max exceeded)
    you should see explanation, not retry. The difference is the lesson.
    """
    # if random.random() < 0.30:
    #     time.sleep(0.2)
    #     raise RuntimeError("simulated upstream timeout")
    pass


def get_customer(name: str | None = None, email: str | None = None) -> dict[str, Any]:
    _maybe_chaos()
    matches = []
    for c in FIXTURES["customers"]:
        if name and c["name"].lower() == name.lower():
            matches.append(c)
        elif email and c["email"].lower() == email.lower():
            matches.append(c)
    if not matches:
        return error_response("validation", False, "No customer found with the supplied identifiers.")
    if len(matches) > 1:
        # Multiple matches — return them so the agent can ask for clarification
        # rather than picking by heuristic. (Domain 5 escalation pattern.)
        return {
            "ambiguous": True,
            "matches": [{"id": c["id"], "email": c["email"]} for c in matches],
            "message": "Multiple customers match. Ask for an additional identifier (email, customer ID, or order number).",
        }
    return matches[0]


def lookup_order(order_id: str) -> dict[str, Any]:
    _maybe_chaos()
    o = FIXTURES["orders"].get(order_id)
    if not o:
        return error_response("validation", False, f"No order found with ID {order_id}.")
    return {"order_id": order_id, **o}


def process_refund(order_id: str, amount: float, customer_id: str) -> dict[str, Any]:
    _maybe_chaos()
    order = FIXTURES["orders"].get(order_id)
    if not order:
        return error_response("validation", False, f"No order found with ID {order_id}.")
    if order["customer_id"] != customer_id:
        return error_response(
            "permission", False,
            f"Order {order_id} does not belong to customer {customer_id}.",
        )
    days = order.get("days_since_delivery")
    window = FIXTURES["policies"]["refund_window_days"]
    if days is None or days > window:
        return error_response(
            "business", False,
            f"Refund window of {window} days has expired for order {order_id}.",
        )
    return {
        "ok": True,
        "refund_id": f"RF-{order_id}",
        "amount_refunded": amount,
        "message": "Refund processed.",
    }


def escalate_to_human(customer_id: str = "", summary: str = "", recommended_action: str = "") -> dict[str, Any]:
    _maybe_chaos()
    return {
        "ok": True,
        "ticket_id": f"ESC-{int(time.time())}",
        "handoff": {
            "customer_id": customer_id,
            "summary": summary,
            "recommended_action": recommended_action,
        },
        "message": "Escalated. A human agent will pick this up.",
    }


# Dispatch table the agent loop calls into.
TOOL_HANDLERS = {
    "get_customer": get_customer,
    "lookup_order": lookup_order,
    "process_refund": process_refund,
    "escalate_to_human": escalate_to_human,
}
