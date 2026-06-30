# Capability Harness

> Capability Harness treats AI as a reasoning engine—not as the operating system.

> The framework owns process. Capabilities own reasoning. Models own inference. Providers own transport.

A deterministic operating system for AI-assisted software engineering. Not an agent framework.

---

## What is Capability Harness?

Capability Harness is a framework for orchestrating AI-assisted software engineering workflows where **deterministic software always drives the process**. AI performs reasoning; the framework performs orchestration.

Traditional agent frameworks let AI decide what to do next. Capability Harness inverts this: the scheduler, policy engine, and routing engine own all workflow decisions. AI capabilities receive structured input, perform reasoning, and return structured output. Nothing more.

**Key properties:**
- **Deterministic orchestration** — workflows are graphs executed by the scheduler, not emergent AI behavior
- **Interchangeable capabilities** — capabilities are declarative specs; implementations are swappable
- **Provider agnostic** — only the Runtime layer knows about Anthropic, OpenAI, Ollama, etc.
- **Artifact-first** — every stage consumes and produces structured artifacts; no ephemeral conversation state
- **Human approval by default** — the merge policy requires explicit approval before any code lands
- **Observable** — every capability execution emits structured telemetry

---

## How It Works

```
Scheduler
   ↓
Capability Graph     — every task runs through a graph, even single-capability tasks
   ↓
Policy Engine        — defines merge policy, retry, routing, token budgets, concurrency
   ↓
Routing Engine       — selects local vs cloud runtime based on WorkProfile + policy
   ↓
Capability Registry  — declarative spec registry; no model knowledge here
   ↓
Runtime              — the only layer that knows about providers
```

**Artifacts are the unit of collaboration.** The scheduler manages artifacts; capabilities transform them. Conversations are implementation details, not system state.

---

## Quick Start

```bash
pip install capability-harness

# Create a project config
cap config validate --config examples/harness.toml

# Submit a task (skeleton noop capability)
cap task submit --capability noop

# List registered capabilities
cap capability list

# Show benchmark metrics
cap benchmark report
```

---

## Core Concepts

### Capabilities
Declarative specs (`capability.toml`) describing what a unit of work needs and produces — never which model or provider to use. The Routing Engine and Runtime handle that.

### Artifacts
The seven standard artifacts: `requirements.md`, `architecture.md`, `implementation_plan.json`, `patch.diff`, `test_report.json`, `review.md`, `telemetry.json`. Content-addressed, sha256-verified.

### Memory Layers
Five layers loaded from lowest to highest specificity: Repository → Architecture → Project → Task → Scratchpad. Capabilities declare which layers they need; the framework loads only those.

### Policy Engine
All configurable project behavior lives here: merge policy (human/auto), approval, retry, routing, token budgets, concurrency limits, provider allowlists. The scheduler executes policy; it never defines it.

### Capability Graph
Workflows are DAGs executed by the scheduler. `Plan → Code → Review → Document` is a graph, not hardcoded control flow. Capabilities never modify the graph.

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full architectural reference.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
