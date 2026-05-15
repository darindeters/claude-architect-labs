# Lab 2 — Multi-agent research with parallel subagents and provenance

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 2.
A coordinator orchestrates four subagents (web search, document analysis,
synthesis, report generation) over a fake but realistic research corpus
with a planted contradiction so you can practice provenance preservation.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 2 — seven recipes; each one maps to a flag or TODO in this scaffold.)

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)
- ~$10 budget (multi-agent runs make more API calls than Lab 1)

## Setup

```bash
cd lab2-research
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python -m src.main "impact of AI on creative industries"
```

The default coordinator prompt is deliberately *procedural and narrow* —
this is the failure case from Question 7 of the sample exam. Recipe 3 of
the lab is to swap it for a goals-and-criteria prompt and see the report
widen.

## Recipes → files

| Recipe | What you do | Where you work |
|---|---|---|
| **1 — Coordinator + four subagents** | Read the four `AgentDefinition`s. Notice each one's `allowed_tools` is tightly scoped. The coordinator separately uses `Task`-style spawning via `dispatch()`. | `src/subagents.py`, `src/coordinator.py` (already done) |
| **2 — Parallel spawning** | Flip `PARALLEL_SPAWN` to `False` and re-run; compare timings printed by the dispatcher. Expected: parallel is at least 2× faster than sequential on a 3+ way fan-out. | `src/coordinator.py` — `PARALLEL_SPAWN` constant |
| **3 — Force the decomposition failure** | Swap `ACTIVE_COORDINATOR_PROMPT` from `COORDINATOR_PROMPT_PROCEDURAL` to `COORDINATOR_PROMPT_GOALS`. Run on `"impact of AI on creative industries"` both ways and compare what sub-domains each report covers. | `src/coordinator.py` — `ACTIVE_COORDINATOR_PROMPT` |
| **4 — Structured findings** | Tighten the synthesis subagent's prompt so every claim carries `{claim, evidence_excerpt, source_url, source_name, publication_date}` forward. The TODO marker is in place. | `src/subagents.py` — `SYNTHESIS.system_prompt` |
| **5 — Conflict annotation** | Add a third document with a same-date contradiction in `fixtures/documents/`. Verify both values appear in the final report with attribution; verify date-separated values are framed as temporal, not contradictory. | `fixtures/documents/` (add file); `src/subagents.py` (prompt tightening) |
| **6 — Scoped `verify_fact` tool** | Add `"verify_fact"` to `SYNTHESIS.allowed_tools`, implement the corresponding handler in the dispatcher, and update the synthesis prompt to call it for single-numeric-claim verifications only. | `src/subagents.py` — `SYNTHESIS.allowed_tools` |
| **7 — Web-search timeout** | Flip `SIMULATE_TIMEOUT` to `True` and re-run. Verify the final report contains an explicit `Coverage gap` section naming the failed query — not a silent partial answer. | `src/coordinator.py` — `SIMULATE_TIMEOUT` constant |

## Naming notes (guide vs scaffold)

| Guide pseudocode | Scaffold reality |
|---|---|
| `AgentDefinition(allowedTools=...)` | `AgentDefinition(allowed_tools=...)` (snake_case; Python convention) |
| Structured timeout: `attemptedQuery`, `partialResults` | `attempted_query`, `partial_results` (snake_case throughout) |
| Coordinator calls `Task(subagent=..., prompt=...)` | The scaffold uses a `ThreadPoolExecutor` over `invoke_subagent(name, prompt)` for clarity — same semantics, fewer SDK moving parts |

The lessons (parallel vs serial timing, decomposition prompts, provenance,
conflict handling, coverage-gap signaling) survive the naming differences.
Use whatever names the scaffold uses when you're coding; use the guide for
the why.

## What success looks like

- Parallel-spawn version runs at least 2× faster than sequential.
- Procedural prompt produces a narrow report; goals-and-criteria prompt
  covers more ground (more sub-domains explicitly named).
- A planted contradiction in `fixtures/documents/` shows up in the final
  report as **two annotated values with attribution**, not one silently
  chosen. A date-separated apparent contradiction is reported as a temporal
  difference, not a disagreement.
- Killing the search subagent mid-run (the `SIMULATE_TIMEOUT` flag)
  produces a report with explicit coverage-gap notes — not a silent partial
  answer marked as success.

See the full walkthrough at <https://learn.techwithdarin.com/certs/claude-architect/#lab>.
