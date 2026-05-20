# Lab 2 — Multi-agent research with parallel subagents and provenance

Starter scaffold for **Claude Certified Architect (Foundations)** Lab 2.
A coordinator orchestrates four subagents (web search, document analysis,
synthesis, report generation) over a fake but realistic research corpus
with a planted contradiction so you can practice provenance preservation.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 2 — seven recipes; each one maps to a flag or TODO in this scaffold.)

> **First time running these labs?** Read the [pitfalls section in the root
> README](../README.md#read-this-first--five-things-that-will-save-you-20-minutes)
> first — Python version, shell quoting, and "what TODO stubs do by default."

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- ~$10 budget (multi-agent runs make more API calls than Lab 1; the parallel-vs-sequential
  timing comparison alone runs the full pipeline twice)

## Setup

```bash
cd lab2-research
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # then edit .env and add your key
```

## First run — confirm the pipeline works

```bash
python -m src.main "impact of AI on creative industries"
```

Expected output, roughly:

```
[coordinator] decomposing: 'impact of AI on creative industries'
[coordinator] 3 subtasks:
  - [web_search] AI tools used in visual arts
  - [web_search] AI in music production
  - [doc_analysis] analyze recent reports on AI in creative work
[coordinator] dispatching subagents...
[coordinator] dispatch took 14.32s (parallel)
[coordinator] synthesizing...
[coordinator] generating report...

# AI Impact on Creative Industries

## Visual Arts
...
```

Total wall-clock is typically 35–55 seconds. The first `[coordinator]` line and the final
markdown report are what to confirm. The subtask list is **decomposition output** — note
how narrow it is. The default `ACTIVE_COORDINATOR_PROMPT = COORDINATOR_PROMPT_PROCEDURAL`
is deliberately bad; the report will under-cover music, writing, and film. **That's
intentional** — recipe 3 is to swap the prompt and watch the report widen.

**If you see something else:**

- *`[coordinator] could not parse decomposition: ...`* → The model returned malformed JSON
  for its subtask list. Usually a one-off; re-run. If it keeps happening, pick a different
  topic.
- *Final report is empty or one paragraph* → Look for `[coordinator] 0 subtasks` in the log.
  Decomposition failed; the synthesis step still ran but had only the local fixture
  documents to work from.
- *`anthropic.AuthenticationError`* → API key not in env. Check `echo $ANTHROPIC_API_KEY`.
- *`TypeError: unsupported operand type(s) for |`* → Python 3.9. Make a fresh venv with 3.10+.

## The fixtures

`fixtures/documents/` ships four planted documents:

| File | Topic | Notable |
|---|---|---|
| `visual_arts.txt` | AI in visual art (2024 data) | Standard reference |
| `music_2024.txt` | AI in music production | Cites a "23% of new tracks use AI" stat (2024) |
| `music_2025.txt` | AI in music production | Cites a "41% of new tracks use AI" stat (2025) — **temporal change vs music_2024** |
| `writing_publishing.txt` | AI in publishing | Standard reference |

The `music_2024` ↔ `music_2025` pair is the planted "contradiction" that's actually a
temporal change. Recipe 5 tests whether your synthesis prompt distinguishes temporal
change from real disagreement.

## Lab toggles — the constants you flip

All in `src/coordinator.py`:

| Constant | Default | What it does |
|---|---|---|
| `PARALLEL_SPAWN` | `True` | `True` → fan out subagents concurrently via `ThreadPoolExecutor`. `False` → sequential. **Recipe 2** flips this and times both. |
| `ACTIVE_COORDINATOR_PROMPT` | `COORDINATOR_PROMPT_PROCEDURAL` | Procedural ("Step 1: search…") vs `COORDINATOR_PROMPT_GOALS` (goals + criteria). **Recipe 3** swaps these. |
| `SIMULATE_TIMEOUT` | `False` | When `True`, the `web_search` subagent short-circuits with a structured timeout payload. **Recipe 7** flips this. |

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

## What you should see per recipe

### Recipe 2 — Parallel vs sequential timing

Run with the default (`PARALLEL_SPAWN = True`):

```bash
time python -m src.main "compare AWS Bedrock, Vertex AI, and Azure Foundry"
```

Look for the dispatch timing line:

```
[coordinator] dispatch took 12.4s (parallel)
```

…and `time`'s total wall-clock around 30–40s.

Now edit `src/coordinator.py`: `PARALLEL_SPAWN = False`. Re-run:

```
[coordinator] dispatch took 34.7s (sequential)
```

Wall-clock around 55–75s. The speedup ratio is `t_sequential / t_parallel` ≈ 2.5–3.5×.
If you see less than 1.5×, your subagents are completing faster than the coordinator
overhead — pick a topic that produces more subtasks.

Restore `PARALLEL_SPAWN = True` when done.

### Recipe 3 — Decomposition failure vs goals

**Default — procedural prompt** (`ACTIVE_COORDINATOR_PROMPT = COORDINATOR_PROMPT_PROCEDURAL`):

```bash
python -m src.main "impact of AI on creative industries"
```

Expected: subtask list dominated by visual arts; music/writing/film barely mentioned in the
final report:

```
[coordinator] 3 subtasks:
  - [web_search] AI in visual arts
  - [web_search] AI tools in design
  - [doc_analysis] analyze provided documents
```

**After swap** to `COORDINATOR_PROMPT_GOALS`:

```python
# in src/coordinator.py
ACTIVE_COORDINATOR_PROMPT = COORDINATOR_PROMPT_GOALS
```

Re-run the same topic. Expected: more subtasks, broader coverage:

```
[coordinator] 5 subtasks:
  - [web_search] AI in visual arts
  - [web_search] AI in music production
  - [web_search] AI in writing and publishing
  - [web_search] AI in film and video
  - [doc_analysis] analyze provided documents on creative industries
```

The final report covers all the sub-domains the procedural prompt missed. Both reports
side-by-side is the lesson — same model, same fixtures, only the coordinator prompt changed.

### Recipe 7 — Simulated web-search timeout

Set `SIMULATE_TIMEOUT = True` in `src/coordinator.py`. Re-run any topic that produces a
`web_search` subtask:

```bash
python -m src.main "energy storage trends 2024"
```

Expected: the `web_search` subagent now returns a structured error payload instead of a
search result. Watch the synthesis step's behavior — does it acknowledge the missing data
or silently produce a partial report?

```
[coordinator] dispatching subagents...
# (web_search returns isError: true with partial_results + alternative_approaches)
[coordinator] synthesizing...
[coordinator] generating report...

# Energy Storage Trends 2024

## Coverage gap
The web-search subagent timed out for this query. The findings below are
based on document analysis only; web-based 2024 reports were not incorporated.

## Findings
...
```

If the report doesn't acknowledge the gap, your synthesis prompt isn't catching the error
shape — strengthen the `SYNTHESIS` subagent's system prompt to handle `isError: true`
inputs explicitly.

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
