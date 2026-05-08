# Lab 2 — Multi-agent research with parallel subagents and provenance

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 2.
A coordinator orchestrates four subagents (web search, document analysis,
synthesis, report generation) over a fake but realistic research corpus
with a planted contradiction so you can practice provenance preservation.

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
this is the failure case from Question 7 of the sample exam. Step 3 of
the lab is to swap it for a goals-and-criteria prompt and see the
report widen.

## Lab steps mapped to files

| Step | Where you work |
|---|---|
| 1 — Coordinator + 4 subagents | Already wired in `src/coordinator.py` and `src/subagents.py` |
| 2 — Parallel spawning | `src/coordinator.py` — flip `PARALLEL_SPAWN` and time both |
| 3 — Force decomposition failure | `src/coordinator.py` — swap `COORDINATOR_PROMPT_*` constants |
| 4 — Claim-source mappings | `src/subagents.py` — fill in the synthesis subagent's output schema |
| 5 — Conflict annotation | Add a third document; verify both values appear in the report |
| 6 — Scoped `verify_fact` tool | `src/subagents.py` — add to synthesis subagent's allowed tools |
| 7 — Web-search timeout | `src/coordinator.py` — flip `SIMULATE_TIMEOUT` and verify error context |

## What success looks like

- Parallel-spawn version runs at least 2× faster than sequential
- Procedural prompt produces a narrow report; goals-and-criteria prompt covers more ground
- A planted contradiction in `fixtures/documents/` shows up in the final report as **two annotated values with attribution**, not one silently chosen
- Killing the search subagent mid-run produces a report with explicit coverage-gap notes — not a silent partial answer
