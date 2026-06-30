# ADR 0004: Routing Engine Between Policy and Registry

## Status
Accepted

## Context

When implementing the scheduler, the question arose: who decides whether a capability runs locally (Ollama) vs in the cloud (Anthropic/OpenAI)? Initial designs had the Scheduler make this decision, or the Capability Registry return an implementation with a model baked in. Both were wrong.

- Putting routing in the Scheduler bloated it with concerns unrelated to workflow.
- Baking model/provider into the Capability Registry broke provider-agnosticism.

## Decision

Insert a **Routing Engine** (`application/routing.py`) between the Policy Engine and the Capability Registry.

**Pipeline:**
```
Scheduler → Capability Graph → Policy Engine → Routing Engine → Capability Registry → Runtime
```

**Routing Engine responsibilities:**
- Consult `RoutingPolicy` from the Policy Engine
- Read the capability's `WorkProfile` (priority, quality, latency_expectation, cost_sensitivity)
- Select a concrete Runtime from the ProviderRegistry
- Apply fallback chain if the preferred runtime is unavailable

**Routing Engine does NOT:**
- Know capability names or specs in detail (it receives a `CapabilitySpec` but delegates to the Runtime)
- Know provider API keys or endpoints (those are in the Runtime implementations)

## Alternatives Considered

- **Routing in the Scheduler**: rejected — Scheduler already owns workflow sequencing; adding routing bloats it
- **Routing in the Capability spec** (`execution_preference = "cloud"`): partially rejected — WorkProfile hints are allowed, but the final decision is the Routing Engine's, not the spec's

## Consequences

- Capabilities are truly provider-agnostic at the spec level
- Routing logic is testable in isolation (mock ProviderRegistry, assert which runtime is selected)
- Adding a new runtime (e.g., a fine-tuned local model) requires only registering it in ProviderRegistry and adjusting RoutingPolicy — no spec changes
