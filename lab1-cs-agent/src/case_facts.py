"""
Case-facts extraction (Step 6).

In long conversations, progressive summarization loses numbers, dates, and
customer-stated expectations. The fix is to extract them into a persistent
structured block included in *every* prompt, outside the summarized history.

Your job: implement extract_case_facts() and inject_case_facts() and wire
them into agent.py. Run a 20-turn conversation and verify nothing important
degrades into vague summary.
"""
from typing import Any


# The canonical case-facts shape used in the walkthrough.
# Start with this exact structure — it makes a turn-3 amount answerable at
# turn 18 because every field is concrete and comparable. Avoid free-text
# "summary" fields here; summaries drift, structured facts don't.
CASE_FACTS_TEMPLATE: dict[str, Any] = {
    "customer_id": None,
    "order_ids": [],
    "amounts_discussed": [],          # e.g., [89.99, 245.00]
    "dates_mentioned": [],            # e.g., ["2026-04-12"]
    "customer_expectations": [],      # e.g., ["full refund + shipping"]
}


def extract_case_facts(messages: list[dict]) -> dict[str, Any]:
    """Walk the conversation history and pull transactional facts.

    Should accumulate, into the CASE_FACTS_TEMPLATE shape:
      - customer_id (from a successful get_customer tool_result)
      - order_ids   (from any successful lookup_order or process_refund call)
      - amounts_discussed (from refund requests in user messages and tool results)
      - dates_mentioned   (delivery dates, refund-window references)
      - customer_expectations (free-text intents stated by the user)
    """
    # TODO (recipe 6): parse tool_use blocks and tool_result blocks from
    # messages and accumulate into a copy of CASE_FACTS_TEMPLATE.
    # Start simple — pull customer_id from get_customer results, and
    # order_ids from any tool input/result referencing one.
    facts = {k: (list(v) if isinstance(v, list) else v) for k, v in CASE_FACTS_TEMPLATE.items()}
    return facts if any(facts.values()) else {}


def inject_case_facts(system_prompt: str, facts: dict[str, Any]) -> str:
    """Prepend a structured case-facts block to the system prompt."""
    if not facts:
        return system_prompt
    block = "## Case facts (load-bearing — do not lose track of these)\n"
    for k, v in facts.items():
        block += f"- {k}: {v}\n"
    return block + "\n" + system_prompt
