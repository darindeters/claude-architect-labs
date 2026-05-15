# Lab 1 — Customer support agent with hook-enforced prerequisites

A starter scaffold for **Claude Certified Architect (Foundations)** Lab 1.
This is the *fast pass*: the loop, four MCP-style tools, fixtures, and hook
placeholders are wired up so you can focus on the exam-relevant judgments
instead of plumbing.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 1 — six recipes; each one maps to a TODO in this scaffold.)

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

## Recipes → files

The walkthrough in the guide breaks Lab 1 into six recipes. Each one points
at a specific TODO in this scaffold. Work them in order.

| Recipe | What you do | Where you work |
|---|---|---|
| **1 — Scaffold an Agent SDK loop** | Read `src/agent.py`. The loop is provided so you can focus on the lessons; understand it before moving on. | `src/agent.py` (already done) |
| **2 — Implement four MCP tools** | Rewrite each tool description from vague (provided) to tight (your job). Run the misroute scenarios before and after; the diff is the lesson. | `src/tools.py` — `TOOLS` list, each `description` |
| **3 — Add a programmatic prerequisite** | Implement `verify_customer_first` so `process_refund` and `lookup_order` are blocked until `get_customer` has set `state["verified_customer_id"]`. | `src/hooks.py` — `verify_customer_first` |
| **4 — Add a refund-threshold hook** | Implement `block_refund_above(500.0)` so refunds over $500 redirect to `escalate_to_human` with a structured handoff payload. | `src/hooks.py` — `block_refund_above` |
| **5 — Add structured errors** | Uncomment the chaos injection in `_maybe_chaos`. Confirm the agent retries `isRetryable=True` failures and explains business-rule failures. The `error_response()` helper is your error shape. | `src/tools.py` — `_maybe_chaos`, and the existing `error_response` use |
| **6 — Add a case-facts persistent block** | Implement `extract_case_facts()` so customer_id, order_ids, amounts, dates, and stated expectations carry forward across turns. The shape is pre-populated in the scaffold so you only write the extraction logic. | `src/case_facts.py` — `extract_case_facts` |

## Naming notes (guide vs scaffold)

The walkthrough uses slightly compressed pseudocode in places where this
scaffold is more production-shaped. The semantics are identical; the names
differ. Use this table to translate.

| Guide pseudocode | Scaffold reality |
|---|---|
| `error(category, message, retryable)` | `error_response(category, retryable, message)` (same fields, kwargs work) |
| `before_process_refund(input, state) -> {"blocked": True, ...}` | `verify_customer_first(state, tool_name, tool_input) -> {"allow": False, "redirect": {...}}` (allow/redirect protocol consumed by the hook chain) |
| Error categories: `transient \| business_rule \| auth` | `transient \| validation \| business \| permission` (`business` is the canonical name; the guide's `business_rule` means the same) |

Either set of names produces the same exam-relevant behavior. The scaffold's
versions are what `agent.py` actually consumes; pick those if you're cutting
and pasting.

## What success looks like

- Asking for a refund of $750 triggers `escalate_to_human` instead of
  `process_refund`, even with a system prompt that insists on auto-approval.
- Removing the prerequisite hook lets the agent occasionally skip
  `get_customer`; restoring it makes the violation impossible.
- A 30%-rate transient failure (uncomment the chaos line in `tools.py`)
  produces retries; a business-rule failure (refund window expired, customer
  mismatch) produces an explanation rather than a retry.
- A turn-18 question about an amount mentioned at turn 3 answers with the
  exact figure once `extract_case_facts` is populated — and drifts to
  hand-wavy without it.

See the full walkthrough at <https://learn.techwithdarin.com/certs/claude-architect/#lab>.
