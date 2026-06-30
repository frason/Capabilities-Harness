# ADR 0005: Runtime as the Sole Provider-Aware Layer

## Status
Accepted

## Context

Provider SDK imports (Anthropic, OpenAI, Ollama, MCP) leaked into multiple layers in early prototypes. This created tight coupling to specific providers, made testing require real API credentials, and meant changing a provider touched many files.

Additionally, the scope of "execution" extends beyond calling LLMs: a capability might need to invoke an MCP server, run a Python function, execute a shell command, or call a native tool. The layer needed a broader name and scope.

## Decision

Create an **infrastructure Runtime layer** (`infrastructure/runtime/`) as the sole subsystem that knows about providers.

**Rule (enforced):** Nothing outside `infrastructure/runtime/` may import a provider SDK or MCP client library.

The Runtime layer contains:
- `Runtime` protocol — `async def run(spec, request) -> WorkResult`
- `ProviderRegistry` — maps names to Runtime implementations
- `NoOpRuntime` — stub for testing and skeleton wiring
- `LocalRuntime` — will invoke Ollama, llama.cpp, Python functions, shell commands
- `CloudRuntime` — will call Anthropic/OpenAI/etc via httpx; provider SDK imports are private here

Provider SDK imports live **only** in `local_runtime.py` and `cloud_runtime.py`, never in public interfaces.

## Alternatives Considered

- **`providers/` package** (one file per provider): rejected — implies symmetrical treatment of providers; "execution" is a better abstraction because it includes non-LLM runtimes
- **Provider SDKs as framework dependencies**: rejected — creates mandatory coupling; users who only use local models shouldn't need `anthropic` installed

## Consequences

- Unit tests use `NoOpRuntime` and never require API credentials
- Adding a new provider requires only a new `Runtime` implementation registered in `ProviderRegistry` — no changes to application layer
- The grep check `rg 'import anthropic|import openai' --include="*.py" -l` should return only files in `infrastructure/runtime/`
