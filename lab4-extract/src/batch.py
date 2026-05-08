"""
Step 6: batch processing via the Message Batches API.

DO NOT open this until extract.py is reliable on at least 5 documents.
The lesson is to not debug two layers at once.

The Message Batches API:
  - 50% cost savings vs synchronous
  - Up to 24-hour processing window, no latency SLA
  - No multi-turn tool calling — you can't do validation-retry inside a batch
  - custom_id correlates request/response pairs

Failure-handling pattern:
  1. Submit all 100 docs with custom_id = doc filename
  2. Poll until done
  3. For each failed doc (by custom_id), modify (e.g., chunk if too long)
     and resubmit only the failures
"""
from __future__ import annotations
from pathlib import Path
from anthropic import Anthropic

from .schema import INVOICE_TOOL_SCHEMA
from .extract import SYSTEM


client = Anthropic()
MODEL = "claude-sonnet-4-5"


def submit_batch(documents: dict[str, str]) -> str:
    """Submit a batch of {custom_id: document_text}. Returns batch ID.

    TODO (step 6): use client.messages.batches.create with one request
    per document. Each request:
      custom_id = the dict key
      params = {model, max_tokens, system, tools, tool_choice, messages}
    Return the batch.id.
    """
    raise NotImplementedError("step 6 of the lab")


def poll_until_done(batch_id: str, interval_seconds: int = 60) -> None:
    """Poll until the batch is complete (or fails)."""
    raise NotImplementedError("step 6 of the lab")


def collect_results(batch_id: str) -> dict[str, dict]:
    """Return {custom_id: parsed_invoice_or_error_dict}."""
    raise NotImplementedError("step 6 of the lab")
