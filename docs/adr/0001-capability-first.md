# ADR 0001: Capability-First Design

## Status
Accepted

## Context

AI engineering frameworks commonly use the "agent" abstraction: named autonomous entities that decide what to do next, pick tools, and drive workflow. This works for exploratory tasks but introduces unpredictability, makes behavior hard to audit, and conflates reasoning with orchestration.

We needed a design where AI reasoning could be introduced into software engineering workflows without ceding control of process to AI.

## Decision

Replace the agent abstraction with **capabilities**.

A capability is:
- A **declarative spec** (`capability.toml`) describing what work it needs and what it produces
- **Stateless** — it receives structured input, performs reasoning, returns structured output
- **Interchangeable** — multiple implementations of the same capability spec can be swapped without changing the framework
- **Named by what it does**, not by who it is (e.g., `code`, `review`, `plan` — not `CodingAgent`, `ReviewBot`)

The Scheduler, Graph, Policy Engine, and Routing Engine own orchestration. Capabilities own reasoning only.

## Alternatives Considered

- **Named agents with tool access**: rejected because agents making orchestration decisions breaks determinism and makes execution hard to audit.
- **LLM-as-orchestrator (ReAct/function-calling loop)**: rejected because the framework loses control of workflow, retry policy, merge gates, and cost.

## Consequences

- Capabilities are testable in isolation (stub runtime, fixed input, assert output)
- Swapping a capability implementation does not change the framework
- Capability specs never reference models or providers — this decoupling is enforced throughout
- New capability types can be introduced without modifying framework code
