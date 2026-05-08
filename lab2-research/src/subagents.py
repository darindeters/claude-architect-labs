"""
Subagent definitions.

Each subagent has its own system prompt and tightly-scoped allowed tools.
Subagent context is *isolated* — they do not inherit the coordinator's
conversation history. The coordinator must pass complete findings in the
subagent's user prompt.

Step 4 of the lab: fill in the synthesis subagent's claim-source schema
so attribution survives summarization.

Step 6 of the lab: add a scoped verify_fact tool to the synthesis subagent
for the simple-verification common case.
"""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AgentDefinition:
    name: str
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=list)
    # Note: in the real Agent SDK these would be MCP tool definitions.
    # This scaffold uses simple Python callables for clarity.
    tool_handlers: dict[str, Callable] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Web search subagent
# ---------------------------------------------------------------------------

WEB_SEARCH = AgentDefinition(
    name="web_search",
    system_prompt=(
        "You are a focused web-search subagent. Given a query, return a list "
        "of relevant sources with URL, title, snippet, and publication date. "
        "Return at least three results. If a tool fails, return structured "
        "error context (failure type, attempted query, partial results) — "
        "never a generic 'unavailable' status, never an empty success."
    ),
    allowed_tools=["search"],
)


# ---------------------------------------------------------------------------
# Document analysis subagent
# ---------------------------------------------------------------------------

DOC_ANALYSIS = AgentDefinition(
    name="doc_analysis",
    system_prompt=(
        "You are a document-analysis subagent. Given a document, extract "
        "key claims with structured metadata: claim text, supporting evidence "
        "excerpt, source URL, source name, and publication date. "
        "If two claims in the document conflict, return BOTH with annotation — "
        "do not silently pick one."
    ),
    allowed_tools=["read_document"],
)


# ---------------------------------------------------------------------------
# Synthesis subagent
# ---------------------------------------------------------------------------

# TODO (step 4): expand the synthesis subagent's prompt to require
# claim-source mappings in its output. Each claim should carry forward:
#   { claim, evidence_excerpt, source_url, source_name, publication_date }
# so attribution doesn't get lost during synthesis.
SYNTHESIS = AgentDefinition(
    name="synthesis",
    system_prompt=(
        "You are a synthesis subagent. Combine findings from multiple sources "
        "into a structured report. Preserve source attribution for every claim. "
        "When sources disagree, present BOTH values with attribution; "
        "structure the report to distinguish well-established from contested findings. "
        "Note publication dates so temporal differences aren't read as contradictions."
    ),
    allowed_tools=[
        # TODO (step 6): add "verify_fact" here for the 85% simple-verification case.
    ],
)


# ---------------------------------------------------------------------------
# Report generator subagent
# ---------------------------------------------------------------------------

REPORT_GEN = AgentDefinition(
    name="report_gen",
    system_prompt=(
        "You are a report-generation subagent. Take a synthesis result and "
        "render it as a finished report. Use tables for numerical comparisons, "
        "prose for narrative, and a clearly-marked 'Coverage gaps' section if "
        "any topic area lacks well-supported findings."
    ),
    allowed_tools=[],
)


ALL_SUBAGENTS = {a.name: a for a in [WEB_SEARCH, DOC_ANALYSIS, SYNTHESIS, REPORT_GEN]}
