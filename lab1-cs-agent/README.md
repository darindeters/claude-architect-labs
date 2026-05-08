# Lab 1 — Customer support agent with hook-enforced prerequisites

A starter scaffold for **Claude Certified Architect (Foundations)** Lab 1.
This is the *fast pass*: the loop, four MCP-style tools, fixtures, and hook
placeholders are wired up so you can focus on the exam-relevant judgments
instead of plumbing.

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)
- ~$5 budget (you'll burn most during the misroute-then-fix exercise)

## Setup

```bash
cd lab1-cs-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then edit .env and add your key
```

Or export directly:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python -m src.agent "I need a refund on order ORD-1003"
```

You'll get a working loop with four tools that return canned data from
`fixtures/customers.json`. The deliberate weak spots are documented inline;
your job in the lab is to close them.

## Lab steps mapped to files

| Step | Where you work |
|---|---|
| 1 — Loop control flow | Already done in `src/agent.py`. Read and run. |
| 2 — Tool descriptions | `src/tools.py` — replace each `TODO: weak description` |
| 3 — Prerequisite hook | `src/hooks.py` — implement `verify_customer_first` |
| 4 — Threshold hook | `src/hooks.py` — implement `block_refund_above` |
| 5 — Structured errors | `src/tools.py` — flesh out `error_response()` use |
| 6 — Case facts block | `src/case_facts.py` — implement extraction & injection |

## What success looks like

- Asking for a refund of $750 triggers `escalate_to_human` instead of
  `process_refund`, even with a system prompt that insists on auto-approval
- Removing the prerequisite hook lets the agent occasionally skip
  `get_customer`; restoring it makes the violation impossible
- A 30%-rate transient failure (uncomment the chaos line in `tools.py`)
  produces retries; a business-rule failure produces an explanation

See the full study guide at <https://help.techwithdarin.com/certs/claude-architect/index.html>.
