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


def extract_case_facts(messages: list[dict]) -> dict[str, Any]:
    """Walk the conversation history and pull transactional facts.

    Should accumulate things like:
      - customer_id
      - order_ids mentioned
      - amounts (refund requests, totals discussed)
      - dates (delivery dates, refund window references)
      - customer-stated expectations ("I want full refund + shipping")
    """
    # TODO (step 6): parse tool_use blocks and tool_result blocks from
    # messages and accumulate facts. Start simple — pull customer_id and
    # order_ids from successful tool results.
    return {}


def inject_case_facts(system_prompt: str, facts: dict[str, Any]) -> str:
    """Prepend a structured case-facts block to the system prompt."""
    if not facts:
        return system_prompt
    block = "## Case facts (load-bearing — do not lose track of these)\n"
    for k, v in facts.items():
        block += f"- {k}: {v}\n"
    return block + "\n" + system_prompt
