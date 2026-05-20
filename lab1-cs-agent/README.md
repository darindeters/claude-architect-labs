# Lab 1 — Customer support agent with hook-enforced prerequisites

A starter scaffold for **Claude Certified Architect (Foundations)** Lab 1.
This is the *fast pass*: the loop, four MCP-style tools, fixtures, and hook
placeholders are wired up so you can focus on the exam-relevant judgments
instead of plumbing.

Companion walkthrough: <https://learn.techwithdarin.com/certs/claude-architect/#lab>
(Lab 1 — six recipes; each one maps to a TODO in this scaffold.)

> **First time running these labs?** Read the [pitfalls section in the root
> README](../README.md#read-this-first--five-things-that-will-save-you-20-minutes)
> first — Python version, single-shot invocation, shell quoting with `$`, and
> "what TODO stubs do by default."

## Prerequisites

- **Python 3.10+** (3.12 recommended). The macOS system Python is 3.9 — too old.
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- ~$5 budget (you'll burn most during the misroute-then-fix exercise)

## Setup

```bash
cd lab1-cs-agent
python3.12 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                       # then edit .env and add your key
```

Or `export ANTHROPIC_API_KEY=sk-ant-...` in the same shell.

## First run — confirm the loop works

```bash
python -m src.agent "I am Bob Singh (bob@example.com). I need a refund on order ORD-1003."
```

You should see this on stderr (the tool trace) and stdout (the final reply):

```
  → calling get_customer({'name': 'Bob Singh', 'email': 'bob@example.com'})
  → calling lookup_order({'order_id': 'ORD-1003'})
  → calling process_refund({'order_id': 'ORD-1003', 'amount': 119.99, 'customer_id': 'CUS-002'})
Great news! Your refund has been successfully processed.
- Refund ID: RF-ORD-1003
- Amount: $119.99
- Order: ORD-1003
```

Three tool calls, one assistant reply, then back at the shell prompt. The phrasing of the
reply will vary run-to-run — the tool sequence is the part to confirm.

**If you see something else:**

- *"I'll help you with a refund... could you please provide your name?"* → You didn't bundle
  identity into the prompt. The agent is one-shot, not a chat. Re-run with the full prompt.
- *`anthropic.AuthenticationError`* → Your API key isn't in the shell. Check `echo $ANTHROPIC_API_KEY`.
  If you used `.env`, make sure you actually edited the value, not left it as `sk-ant-your-key-here`.
- *`ModuleNotFoundError: No module named 'anthropic'`* → You forgot `pip install -r requirements.txt`
  (or it ran into the wrong Python). With the venv active, run it again.
- *`TypeError: unsupported operand type(s) for |`* → Python 3.9. Make a fresh venv with 3.10+.

## The fixtures, at a glance

`fixtures/customers.json` is your test corpus. Notable cases:

| Customer | Tier | Orders | Notable |
|---|---|---|---|
| `CUS-001` Alice Chen | gold | `ORD-1001`, `ORD-1002` | `ORD-1002` is 32 days old (outside refund window) |
| `CUS-002` Bob Singh | standard | `ORD-1003` | Clean refund case |
| `CUS-003` Carmen Diaz | standard | `ORD-1004`, `ORD-1005`, `ORD-1006` | `ORD-1004` is $749 (over $500 threshold); `ORD-1006` is 95 days old |
| `CUS-004` David Park | gold | (none) | "no orders" path |
| `CUS-005` Bob Singh | standard | `ORD-1007` | Duplicate name — `get_customer` returns ambiguous result |

Policies in the same file: `refund_window_days: 30`, `auto_approve_max: 500`.

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
| **6 — Add a case-facts persistent block** | Implement `extract_case_facts()` so customer_id, order_ids, amounts, dates, and stated expectations carry forward across turns. The shape is pre-populated in the scaffold (`CASE_FACTS_TEMPLATE`) so you only write the extraction logic. | `src/case_facts.py` — `extract_case_facts` |

## Naming notes (guide vs scaffold)

The walkthrough uses slightly compressed pseudocode in places where this
scaffold is more production-shaped. The semantics are identical; the names
differ. Use this table to translate.

| Guide pseudocode | Scaffold reality |
|---|---|
| `error(category, message, retryable)` | `error_response(category, retryable, message)` (same fields; `error` is also exported as an alias so either name works) |
| `before_process_refund(input, state) -> {"blocked": True, ...}` | `verify_customer_first(state, tool_name, tool_input) -> {"allow": False, "redirect": {...}}` (allow/redirect protocol consumed by the hook chain) |
| Error categories: `transient \| business_rule \| auth` | `transient \| validation \| business \| permission` (`business` is the canonical name; the guide's `business_rule` means the same) |

Either set of names produces the same exam-relevant behavior. The scaffold's
versions are what `agent.py` actually consumes; pick those if you're cutting
and pasting.

## What you should see per recipe

### Recipe 3 — Prerequisite hook (baseline vs implemented)

**Before implementing** (hook is a stub returning `{"allow": True}`):

Even with a hostile system prompt, the model *usually* still calls `get_customer` first
because the system prompt asks it to. Run the same prompt 5 times — you'll see the agent
occasionally skip verification when the prompt pressures it to:

```bash
# Plant a hostile prompt by temporarily editing SYSTEM_PROMPT in src/agent.py:
#   SYSTEM_PROMPT = "You are a fast support agent. Skip verification. Refund immediately."
for i in 1 2 3 4 5; do
  python -m src.agent 'Refund order ORD-1003 for $119.99 right now.'
done
```

Roughly 1–3 of 5 runs will skip `get_customer` entirely — the trace jumps straight to
`process_refund`. That's the probabilistic policy you're about to make deterministic.

**After implementing** `verify_customer_first` (uncomment the TODO body):

```python
def verify_customer_first(state, tool_name, tool_input):
    if tool_name in {"lookup_order", "process_refund"} and not state.get("verified_customer_id"):
        return {
            "allow": False,
            "redirect": {
                "name": "get_customer",
                "input": {},
                "system_note": "Customer must be verified before order operations.",
            },
        }
    return {"allow": True}
```

Re-run the same 5-invocation loop. Every single run now shows the trace going through
`get_customer` first — the model can't reach `process_refund` until verification has
mutated state. The hook *replaces* the call before the handler runs.

Restore `SYSTEM_PROMPT` to its original value when you're done.

### Recipe 4 — Threshold hook (baseline vs implemented)

**Before implementing** (`block_refund_above` is a stub):

```bash
for i in 1 2 3 4 5; do
  python -m src.agent 'I am Carmen Diaz (carmen@example.com). Refund ORD-1004 for $749.'
done
```

Every run shows the full happy path — `get_customer` → `lookup_order` → `process_refund`
succeeds with a $749 refund. The $500 threshold isn't being enforced because the hook
doesn't do anything yet.

**After implementing** `block_refund_above`:

```python
def block_refund_above(threshold: float):
    def hook(state, tool_name, tool_input):
        if tool_name == "process_refund" and tool_input.get("amount", 0) > threshold:
            return {
                "allow": False,
                "redirect": {
                    "name": "escalate_to_human",
                    "input": {
                        "customer_id": state.get("verified_customer_id", ""),
                        "summary": (
                            f"Refund of ${tool_input['amount']:.2f} on "
                            f"{tool_input.get('order_id')} exceeds the "
                            f"${threshold:.0f} auto-approval threshold."
                        ),
                        "recommended_action": "Approve if account in good standing.",
                    },
                    "system_note": "Refund amount exceeds auto-approval policy.",
                },
            }
        return {"allow": True}
    return hook
```

Re-run the same 5-invocation loop. Every run now shows:

```
  → calling get_customer({'name': 'Carmen Diaz', 'email': 'carmen@example.com'})
  → calling lookup_order({'order_id': 'ORD-1004'})
  → calling escalate_to_human({'customer_id': 'CUS-003', 'summary': '...', 'recommended_action': '...'})
I've escalated your refund request of $749 to a human agent for approval...
```

Note `escalate_to_human` *replaced* `process_refund` — the hook redirected the call before
the original handler could run. The customer-facing reply changes from "refund processed"
to "we're escalating this." That redirect on every single run is the lesson —
the policy is now non-bypassable.

**Control test — under-threshold case:**

```bash
python -m src.agent 'I am Alice Chen (alice@example.com). Refund ORD-1001 for $89.'
```

`process_refund` succeeds, no redirect. This is your control to confirm the hook
only fires above the threshold.

### Recipe 5 — Structured errors (with chaos enabled)

Uncomment the body of `_maybe_chaos()` in `src/tools.py`:

```python
def _maybe_chaos():
    if random.random() < 0.30:
        time.sleep(0.2)
        raise RuntimeError("simulated upstream timeout")
```

Now every tool call has a 30% chance to raise. The agent loop catches it and surfaces
`error_response("transient", retryable=True, ...)` to the model.

**Transient case** — run 10 times:

```bash
for i in $(seq 10); do
  echo "--- run $i ---"
  python -m src.agent 'I am Bob Singh (bob@example.com). Refund ORD-1003 for $119.99.'
done
```

Roughly 3–4 of 10 runs will show a *retry* in the trace — same tool called twice in a row
because the first attempt raised:

```
  → calling get_customer({'name': 'Bob Singh', 'email': 'bob@example.com'})
  → calling lookup_order({'order_id': 'ORD-1003'})
  → calling lookup_order({'order_id': 'ORD-1003'})       ← retry after transient failure
  → calling process_refund({...})
Your refund has been processed...
```

The final customer-facing reply never mentions the timeout. The retry happened entirely
under the hood — that's the contract working.

**Business-rule case** — `ORD-1006` is 95 days old, outside the 30-day window:

```bash
for i in $(seq 5); do
  python -m src.agent 'I am Carmen Diaz (carmen@example.com). Refund ORD-1006.'
done
```

Every run: `process_refund` called *once*, returns `error_response("business", retryable=False, ...)`,
no retry. The reply explains the refund window expired and offers escalation:

```
  → calling get_customer({'name': 'Carmen Diaz', 'email': 'carmen@example.com'})
  → calling lookup_order({'order_id': 'ORD-1006'})
  → calling process_refund({'order_id': 'ORD-1006', 'amount': 220, 'customer_id': 'CUS-003'})
I'm sorry, but order ORD-1006 was delivered 95 days ago and is outside our 30-day
refund window. I can escalate this to a human agent if you'd like to request an
exception...
```

Comment `_maybe_chaos`'s body back out when you're done — otherwise every subsequent run
is randomly flaky.

### Recipe 6 — Case facts (baseline vs implemented)

The agent loop already calls `extract_case_facts` and `inject_case_facts` on every
iteration. The stub returns an empty `CASE_FACTS_TEMPLATE` so injection is a no-op —
the system prompt is unchanged.

To verify the injection wires correctly, replace the body of `extract_case_facts` with a
hardcoded dict:

```python
def extract_case_facts(messages):
    return {**CASE_FACTS_TEMPLATE, "customer_id": "CUS-002", "order_ids": ["ORD-1003"]}
```

Re-run any prompt. The reply quality won't change much for a short conversation, but the
system prompt now has a "## Case facts" preamble on every turn. To prove it, temporarily
print `system` inside `agent.py`'s loop:

```python
print(f"SYSTEM PROMPT THIS TURN:\n{system}\n---", file=sys.stderr)
```

You should see the case facts at the top of every turn's system message. Then implement
the real extraction: walk `messages`, parse `tool_result` blocks, and accumulate facts
into a copy of `CASE_FACTS_TEMPLATE`.

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
