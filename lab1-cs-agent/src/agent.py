"""
The agent loop.

Domain 1 lesson: the loop terminates on stop_reason, not on any
natural-language signal from the model and not on an iteration cap as
the primary mechanism. Iteration caps are a safety net.

Run:
    python -m src.agent "I need a refund on order ORD-1003"
"""
from __future__ import annotations
import json
import os
import sys
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from .tools import TOOLS, TOOL_HANDLERS
from .hooks import run_pre_tool_hooks
from .case_facts import extract_case_facts, inject_case_facts


load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from env

MODEL = "claude-sonnet-4-5"
MAX_LOOP_ITERATIONS = 20  # safety net only — the real terminator is stop_reason

SYSTEM_PROMPT = """You are a customer support agent for an e-commerce store.
You can verify customers, look up orders, process refunds within policy, and
escalate to a human agent when needed. Always verify the customer before any
order operations. Be concise and helpful."""


def call_tool(state: dict, name: str, tool_input: dict) -> Any:
    """Run hooks, dispatch to the tool, and update state."""
    name, tool_input, note = run_pre_tool_hooks(state, name, tool_input)
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"isError": True, "errorCategory": "validation", "isRetryable": False,
                "message": f"Unknown tool: {name}"}
    try:
        result = handler(**tool_input)
    except Exception as e:
        return {"isError": True, "errorCategory": "transient", "isRetryable": True,
                "message": f"Tool raised: {type(e).__name__}: {e}"}

    # Track verified customer for the prerequisite hook (step 3).
    if name == "get_customer" and isinstance(result, dict) and result.get("id"):
        state["verified_customer_id"] = result["id"]

    if note:
        # Surface the hook's redirect reason to the model.
        if isinstance(result, dict):
            result = {**result, "_hook_note": note}
    return result


def run(user_message: str) -> str:
    state: dict[str, Any] = {"verified_customer_id": None}
    messages = [{"role": "user", "content": user_message}]

    for iteration in range(MAX_LOOP_ITERATIONS):
        # Step 6: enrich the system prompt with extracted case facts each turn.
        facts = extract_case_facts(messages)
        system = inject_case_facts(SYSTEM_PROMPT, facts)

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # The real termination check.
        if response.stop_reason == "end_turn":
            text = "".join(b.text for b in response.content if b.type == "text")
            return text or "(empty response)"

        if response.stop_reason != "tool_use":
            # max_tokens, refusal, etc — bail out.
            return f"[stopped on: {response.stop_reason}]"

        # Append the assistant turn (text + tool_use blocks) to history.
        messages.append({"role": "assistant", "content": response.content})

        # Execute every tool_use block, gather tool_result blocks.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_input = dict(block.input) if block.input else {}
            print(f"  → calling {block.name}({tool_input})", file=sys.stderr)
            result = call_tool(state, block.name, tool_input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": bool(isinstance(result, dict) and result.get("isError")),
            })

        # Append tool results so the model can reason about them next iteration.
        messages.append({"role": "user", "content": tool_results})

    return "[hit safety-net iteration cap — investigate why stop_reason never went to end_turn]"


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent '<customer message>'")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)
    print(run(sys.argv[1]))


if __name__ == "__main__":
    main()
