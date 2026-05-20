# Claude Certified Architect — Foundations: Hands-On Labs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Production-grade Python scaffolds for the practical skills the
[Claude Certified Architect — Foundations](https://www.anthropic.com/learn/claude-architect-certification)
exam tests.** Skip the plumbing; keep the lessons.

The exam guide lists "build the thing" as the most effective prep
strategy. These three labs do the awkward setup work — agent loops,
MCP-style tool definitions, fixtures, schemas — and leave clearly-marked
`TODO` blocks at the exam-relevant decision points.

> Each lab maps directly to a scenario from the official exam guide and
> reinforces the tradeoffs the questions reward.

---

## What's in here

| Lab | Topic | Domains | Time |
|---|---|---|---|
| [`lab1-cs-agent/`](lab1-cs-agent/) | Customer support agent with hook-enforced prerequisites | D1 (Agentic), D2 (Tools), D5 (Reliability) | ~3 hrs |
| [`lab2-research/`](lab2-research/) | Multi-agent research with parallel subagents and provenance | D1, D2, D5 | ~3 hrs |
| [`lab4-extract/`](lab4-extract/) | Structured extraction with validation and batch | D4 (Structured output), D5 | ~2 hrs |

(Labs 3 and 5 from the official guide are configuration-only and
documentation-only respectively — no code scaffold needed.)

---

## Quick start

Pick a lab, hop in, run the boot command.

```bash
git clone https://github.com/darindeters/claude-architect-labs.git
cd claude-architect-labs/lab1-cs-agent

python3.12 -m venv .venv && source .venv/bin/activate    # see Python note below
pip install -r requirements.txt
cp .env.example .env                                     # then edit .env and paste your key
# OR: export ANTHROPIC_API_KEY=sk-ant-...                # one-shot, current shell only

python -m src.agent "I am Bob Singh (bob@example.com). I need a refund on order ORD-1003."
```

Each lab boots in 30 seconds against the [Anthropic API](https://docs.claude.com/en/api/overview).
Total budget across all three: ~$20.

Get your API key at <https://console.anthropic.com/settings/keys> — click "Create Key".

---

## Read this first — five things that will save you 20 minutes

These are the issues every first-time runner hits. Skim them now; come back when you get stuck.

### 1. Python 3.10 or newer is required

If you see this on first run:

```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

…you're on Python 3.9 (the version macOS Command Line Tools ships). The scaffolds use the
`str | None` union syntax from [PEP 604](https://peps.python.org/pep-0604/) which only
landed in 3.10.

Fix on macOS:

```bash
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
python --version           # should print 3.12.x or 3.13.x
pip install -r requirements.txt
```

`python` inside the venv resolves to 3.12 regardless of what `python3` points at globally.

### 2. Each invocation is one-shot, not a chat

The agent isn't an interactive REPL. Every `python -m src.agent "..."` runs the loop to
`stop_reason == "end_turn"`, prints the final reply, and exits. If the model asks for
clarification, you don't type more — you re-run with a fuller prompt.

**Bundle everything the agent needs into the first message:**

```bash
# Bad — the agent will ask "what's your name?" then exit
python -m src.agent "I need a refund on ORD-1003"

# Good — agent gets identity + intent in one shot
python -m src.agent "I am Bob Singh (bob@example.com). I need a refund on order ORD-1003."
```

### 3. Shell `$` interacts with prompts that contain dollar signs

A prompt like `"Refund ORD-1004 for $749"` inside **double quotes** runs into shell variable
expansion: `$7` is an unset variable that expands to empty, and the agent receives
`"Refund ORD-1004 for 49"`. The model can't see the amount and asks you to clarify.

Two fixes — either works:

```bash
# Single quotes (no expansion)
python -m src.agent 'I am Carmen Diaz. Refund ORD-1004 for $749.'

# Or escape the dollar sign inside double quotes
python -m src.agent "I am Carmen Diaz. Refund ORD-1004 for \$749."
```

### 4. TODO stubs in the scaffolds default to "allow everything"

The hooks in `lab1-cs-agent/src/hooks.py` and the validators in `lab4-extract/src/validate.py`
ship as TODO stubs that return permissive defaults. **This is intentional.** Before you
implement the hook for step N, you should see the *baseline* behavior — refunds going
through with no threshold check, totals not being flagged, etc. The lesson is the
before/after comparison. If your first run looks "too permissive," you haven't done the
step yet.

Each step's README block names exactly which TODO to implement and what behavior to expect
afterward.

### 5. Watch stderr for tool traces

The agent prints `→ calling get_customer({...})` lines to **stderr** as each tool fires.
The final assistant text prints to stdout. If you're piping output, you'll lose the trace —
either don't pipe, or redirect with `2>&1`. The trace is the most useful debugging signal
in the loop; learn to read it.

---

## How to use these

These scaffolds are designed to pair with a study guide that walks
through the exam concepts and maps each step to a file in the lab.

📖 **Companion study guide:** <https://learn.techwithdarin.com/certs/claude-architect/>

You can absolutely use the labs without the guide — every `TODO`
in the source is annotated with the step number and the underlying
exam concept. But the guide explains *why* each step is the right
answer, and the question patterns the exam consistently rewards.

### The three working modes

1. **Read-only.** Clone, run the working bits, read the source. Faster
   way to internalize the idiomatic agent loop, the deterministic-vs-probabilistic
   distinction, and the structure of MCP-style error responses than
   anything you'll find in the docs.
2. **TODO-driven.** Clone, run the lab, work through the numbered TODOs.
   This is the intended path. Each TODO block corresponds to a numbered
   step in the official exam guide's preparation exercises.
3. **Whole rewrite.** Use the fixtures and the README's "what success
   looks like" criteria, ignore the source, write your own from scratch.
   Highest learning, slowest path.

---

## Lab 1 — Customer support agent

**Scenario:** A customer support resolution agent backed by four MCP-style
tools (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`).
Target: 80%+ first-contact resolution while knowing when to escalate.

**What you'll practice:**
- Agentic loop control flow (`stop_reason` based termination — no
  iteration caps as the primary stopping mechanism)
- Tool descriptions as the primary tool-selection mechanism (start with
  deliberately weak descriptions; watch the agent misroute; fix them)
- Programmatic prerequisite enforcement via hooks (vs. probabilistic
  prompt-based "please verify the customer first")
- Structured error responses with `errorCategory` / `isRetryable`
- Persistent case-facts blocks vs. progressive summarization

**Boot:** `python -m src.agent "I need a refund on order ORD-1003"`

[→ Lab 1 README](lab1-cs-agent/README.md)

---

## Lab 2 — Multi-agent research

**Scenario:** A coordinator agent dispatches four subagents (web search,
document analysis, synthesis, report generation) to research a topic
and produce a comprehensive cited report.

**What you'll practice:**
- Coordinator-subagent orchestration (hub-and-spoke; isolated subagent
  context; explicit prompt passing)
- Parallel subagent spawning vs. sequential (toggle one constant; time
  both)
- The decomposition failure mode (procedural prompt produces a narrow
  report; goals-and-criteria prompt covers more ground)
- Claim-source mapping preservation across synthesis
- Conflict annotation (two contradictory sources both surface in the
  report with attribution, rather than one silently chosen)
- Structured error context propagation when a subagent fails

**Boot:** `python -m src.main "impact of AI on creative industries"`

[→ Lab 2 README](lab2-research/README.md)

---

## Lab 4 — Structured extraction

**Scenario:** An extraction system that pulls structured data from
unstructured documents, validates the output, and integrates with
downstream systems. Ten invoice fixtures, including five with planted
edge cases.

**What you'll practice:**
- `tool_use` with JSON schemas — the only reliable path to
  schema-compliant structured output
- Required vs. optional (nullable) field design — flip a field to
  required and watch the model fabricate values
- `tool_choice` modes (`"auto"`, `"any"`, forced specific tool)
- Validation-retry loops (resolves format errors, fails when info is
  genuinely absent)
- Few-shot examples for varied document structures
- Self-correction validators (`calculated_total` vs `stated_total`)
- Message Batches API tradeoffs (50% cost savings, no multi-turn tool
  calling, up-to-24-hour latency)

**Boot:** `python -m src.extract fixtures/invoice_001.txt`

[→ Lab 4 README](lab4-extract/README.md)

---

## What this isn't

- **Not exam dumps.** No actual exam questions are reproduced here.
  The labs are derived from the publicly-available [official exam
  guide](https://www.anthropic.com/learn/claude-architect-certification)
  and the preparation exercises it suggests.
- **Not the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) reference implementation.**
  The scaffolds use the plain `anthropic` Python client to keep the
  agent loop visible and runnable without SDK-specific surface area.
  That makes the exam concepts concrete; if you're shipping production
  multi-agent systems, you should also read the Agent SDK docs.
- **Not stubbed.** Every lab boots and runs against the real API.
  The TODOs are the exam-relevant decisions, not "implement everything."

---

## Contributing

PRs welcome — especially:

- Better few-shot examples for Lab 4
- Additional planted edge cases in Lab 2's research fixtures
- Translations of the READMEs
- Notes on what surprised you while working through the lab (these
  often surface real gaps in the scaffold)

For substantive changes, please open an issue first so we can talk it
through. Keep additions focused on the exam concepts; the labs are
deliberately small.

---

## License

[MIT](LICENSE) — use these freely for your own prep, study groups,
internal training programs, or anything else you find useful.

---

## See also

- 📖 [Companion study guide](https://learn.techwithdarin.com/certs/claude-architect/) — the five judgments the exam rewards, seven question patterns, and the day-of strategy
- 📚 [Anthropic Claude documentation](https://docs.claude.com/)
- 🔧 [Claude Agent SDK (Python)](https://github.com/anthropics/claude-agent-sdk-python)
- 🌐 [Model Context Protocol](https://modelcontextprotocol.io)
- 🎓 [Claude Certified Architect — Foundations](https://www.anthropic.com/learn/claude-architect-certification)

Built by [Darin Deters](https://techwithdarin.com) ([@darindeters](https://github.com/darindeters)).
If these saved you time, [buy me a coffee](https://www.buymeacoffee.com/techwithdarin) ☕.
