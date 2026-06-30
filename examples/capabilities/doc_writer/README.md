# doc_writer

An example capability that reads `architecture.md` and produces updated documentation.

## What it does

1. Reads `architecture.md` from the task's input artifacts
2. Loads repository, architecture, and task memory layers
3. Requests execution from the Runtime
4. Produces a `review.md` artifact with the updated documentation

## Usage

```bash
cap task submit --capability doc_writer --input architecture.md
```

## Spec notes

Uses `batch` latency expectation and `cost_optimized` cost sensitivity,
which the Routing Engine will use to prefer lower-cost runtimes.
