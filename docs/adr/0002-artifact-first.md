# ADR 0002: Artifact-First Collaboration

## Status
Accepted

## Context

AI-assisted workflows typically pass state through conversation history: the model generates text, that text is re-injected into the next prompt, and system state is implicit in the conversation. This makes state hard to inspect, persist, or pass between capabilities.

## Decision

**Artifacts are the unit of collaboration.** Every stage consumes structured artifacts and produces structured artifacts. Conversations are implementation details, not system state.

The seven standard artifacts:

| Artifact | Description |
|----------|-------------|
| `requirements.md` | What needs to be built |
| `architecture.md` | How it will be built |
| `implementation_plan.json` | Step-by-step implementation plan |
| `patch.diff` | Code changes (unified diff) |
| `test_report.json` | Structured test results |
| `review.md` | Human or AI review output |
| `telemetry.json` | Execution metrics and spans |

Artifacts are:
- **Content-addressed** (sha256) for integrity verification
- **Persisted** by the ArtifactStore independent of the capability that produced them
- **Typed** — each kind has a schema; capabilities receive typed models, not raw strings

## Alternatives Considered

- **Conversation-first**: rejected — implicit state, no persistence, hard to debug
- **Database-first** (structured tables for all state): rejected — over-engineered for the artifact types we need; files are simpler and git-friendly

## Consequences

- Capability outputs are inspectable with `cap artifact get`
- Artifacts survive process restarts (stored on filesystem)
- The ReviewCompleted and MergeApproved gates reference artifact content, not conversation
- Telemetry is itself an artifact, making benchmarking straightforward
