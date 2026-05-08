"""
Programmatic enforcement hooks.

These are where Domain 1's deterministic-vs-probabilistic distinction
lives. Prompts can ask the model nicely; hooks make compliance impossible
to bypass.

Step 3: implement verify_customer_first — block process_refund and
        lookup_order until get_customer has returned a verified ID.

Step 4: implement block_refund_above — intercept outgoing process_refund
        calls over a threshold and redirect to escalate_to_human.

Each hook returns either:
  {"allow": True} — let the call through unchanged
  {"allow": True, "transform": <new_input>} — let it through, modified
  {"allow": False, "redirect": <new_tool_call>} — replace with another call
"""
from typing import Any


# ---------------------------------------------------------------------------
# Step 3: prerequisite hook
# ---------------------------------------------------------------------------

def verify_customer_first(state: dict[str, Any], tool_name: str, tool_input: dict) -> dict[str, Any]:
    """Block lookup_order and process_refund until a verified customer ID exists.

    state['verified_customer_id'] is set by the agent loop after a
    successful get_customer call. This hook reads it.
    """
    # TODO (step 3): if tool_name in {"lookup_order", "process_refund"} and
    # state.get("verified_customer_id") is None, return:
    #   {
    #     "allow": False,
    #     "redirect": {
    #       "name": "get_customer",
    #       "input": {},
    #       "system_note": "Customer must be verified before order operations.",
    #     },
    #   }
    # otherwise return {"allow": True}.
    return {"allow": True}


# ---------------------------------------------------------------------------
# Step 4: threshold hook
# ---------------------------------------------------------------------------

def block_refund_above(threshold: float):
    """Return a hook that blocks process_refund calls above `threshold`."""
    def hook(state: dict[str, Any], tool_name: str, tool_input: dict) -> dict[str, Any]:
        # TODO (step 4): if tool_name == "process_refund" and
        # tool_input.get("amount", 0) > threshold, return a redirect to
        # escalate_to_human with a structured handoff.
        return {"allow": True}
    return hook


# ---------------------------------------------------------------------------
# Hook chain runner — called by the agent loop before each tool dispatch.
# Returns the (possibly redirected) tool call to actually execute.
# ---------------------------------------------------------------------------

ACTIVE_HOOKS = [
    verify_customer_first,
    block_refund_above(threshold=500.0),
]


def run_pre_tool_hooks(state: dict[str, Any], tool_name: str, tool_input: dict) -> tuple[str, dict, str | None]:
    """Run all hooks; return (final_name, final_input, system_note_or_None)."""
    note = None
    for hook in ACTIVE_HOOKS:
        result = hook(state, tool_name, tool_input)
        if not result.get("allow", True):
            redirect = result["redirect"]
            tool_name = redirect["name"]
            tool_input = redirect.get("input", {})
            note = redirect.get("system_note") or note
    return tool_name, tool_input, note
