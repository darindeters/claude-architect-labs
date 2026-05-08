"""
Coordinator: hub-and-spoke orchestration.

All inter-subagent communication routes through here. The coordinator
decomposes the query, dispatches subagents (in parallel where possible),
collects results, and re-invokes synthesis if coverage is insufficient.

Step 2: PARALLEL_SPAWN — flip to False to time sequential vs parallel.
Step 3: COORDINATOR_PROMPT_PROCEDURAL vs COORDINATOR_PROMPT_GOALS — swap
        to see how prompt shape changes decomposition quality.
Step 7: SIMULATE_TIMEOUT — flip to True to simulate a web-search timeout
        and verify the coordinator gets structured error context.
"""
from __future__ import annotations
import json
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from .subagents import ALL_SUBAGENTS

client = Anthropic()
MODEL = "claude-sonnet-4-5"

PARALLEL_SPAWN = True
SIMULATE_TIMEOUT = False

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Coordinator prompts (Step 3)
# ---------------------------------------------------------------------------

# This is the failure case from Question 7. Procedural and narrow — the
# coordinator decomposes "creative industries" into only visual arts.
COORDINATOR_PROMPT_PROCEDURAL = """\
You are a research coordinator. Decompose the topic into 3 specific subtasks
and dispatch them. Return a list of {subtask, type} objects, where type is
one of: web_search, doc_analysis."""

# This is the corrected version: goals and quality criteria, not procedure.
COORDINATOR_PROMPT_GOALS = """\
You are a research coordinator. Your goal is comprehensive, well-attributed
coverage of the topic across ALL relevant subdomains the topic implies.
For "creative industries" that means at minimum visual arts, music, writing,
and film. Decompose to ensure no major subdomain is silently dropped.
Return a list of {subtask, type} objects, where type is one of:
web_search, doc_analysis."""

ACTIVE_COORDINATOR_PROMPT = COORDINATOR_PROMPT_PROCEDURAL


# ---------------------------------------------------------------------------
# Subagent invocation (simplified — calls Claude with the subagent's
# system prompt and the explicitly-passed context).
# ---------------------------------------------------------------------------

def invoke_subagent(name: str, user_prompt: str) -> dict[str, Any]:
    if name == "web_search" and SIMULATE_TIMEOUT:
        # Step 7: structured error context, not a generic "search unavailable"
        return {
            "isError": True,
            "errorCategory": "transient",
            "isRetryable": True,
            "failure_type": "timeout",
            "attempted_query": user_prompt[:120],
            "partial_results": [],
            "alternative_approaches": [
                "retry with narrower query",
                "fall back to cached search results",
                "proceed with doc_analysis-only and note coverage gap",
            ],
        }

    sub = ALL_SUBAGENTS[name]
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=sub.system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    return {"ok": True, "subagent": name, "output": text}


# ---------------------------------------------------------------------------
# Step 2: parallel vs sequential subagent spawning
# ---------------------------------------------------------------------------

def dispatch(subtasks: list[dict]) -> list[dict]:
    """Run subagent calls in parallel (or sequentially)."""
    started = time.time()
    if PARALLEL_SPAWN:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(invoke_subagent, t["type"], t["subtask"]) for t in subtasks]
            results = [f.result() for f in futures]
    else:
        results = [invoke_subagent(t["type"], t["subtask"]) for t in subtasks]
    print(f"[coordinator] dispatch took {time.time()-started:.2f}s "
          f"({'parallel' if PARALLEL_SPAWN else 'sequential'})")
    return results


# ---------------------------------------------------------------------------
# Decomposition step
# ---------------------------------------------------------------------------

def decompose(query: str) -> list[dict]:
    """Ask Claude to decompose into subtasks based on the active coordinator prompt."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ACTIVE_COORDINATOR_PROMPT,
        messages=[{"role": "user", "content": f"Topic: {query}\n\nReturn JSON only."}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    # Naive parse — find the first JSON array in the response.
    start = text.find("[")
    end = text.rfind("]")
    try:
        return json.loads(text[start:end+1])
    except Exception:
        print(f"[coordinator] could not parse decomposition: {text}")
        return []


# ---------------------------------------------------------------------------
# Synthesis + report
# ---------------------------------------------------------------------------

def synthesize(query: str, search_results: list[dict], doc_analyses: list[dict]) -> str:
    payload = {
        "query": query,
        "search_results": search_results,
        "document_analyses": doc_analyses,
    }
    res = invoke_subagent("synthesis", json.dumps(payload, indent=2))
    return res.get("output", "")


def generate_report(synthesis_output: str) -> str:
    res = invoke_subagent("report_gen", synthesis_output)
    return res.get("output", "")


# ---------------------------------------------------------------------------
# Top-level run
# ---------------------------------------------------------------------------

def run(query: str) -> str:
    print(f"[coordinator] decomposing: {query!r}")
    subtasks = decompose(query)
    print(f"[coordinator] {len(subtasks)} subtasks:")
    for t in subtasks:
        print(f"  - [{t.get('type')}] {t.get('subtask')}")

    print(f"[coordinator] dispatching subagents...")
    results = dispatch(subtasks)
    search_results = [r for r in results if r.get("subagent") == "web_search" or "search" in str(r)]
    doc_analyses = [r for r in results if r.get("subagent") == "doc_analysis"]

    # Inject the local fixture documents directly into the analysis bucket
    # so the synthesis step has the planted-contradiction fixtures in scope.
    doc_dir = FIXTURES_DIR / "documents"
    for doc in sorted(doc_dir.glob("*.txt")):
        doc_analyses.append({"ok": True, "subagent": "doc_analysis", "output": doc.read_text()})

    print(f"[coordinator] synthesizing...")
    synthesis = synthesize(query, search_results, doc_analyses)

    print(f"[coordinator] generating report...")
    return generate_report(synthesis)
