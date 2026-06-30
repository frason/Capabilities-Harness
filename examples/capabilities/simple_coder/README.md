# simple_coder

A minimal example capability that generates Python code from a `requirements.md` artifact.

## What it does

1. Reads `requirements.md` from the task's input artifacts
2. Assembles memory context (repository layer + task layer)
3. Requests execution from the Runtime (cloud by default)
4. Writes generated code to the worktree
5. Produces a `patch.diff` artifact

## Registration

Add to your project's `pyproject.toml`:

```toml
[project.entry-points."capability_harness.capabilities"]
simple_coder = "my_package.simple_coder:SimpleCoderCapability"
```

## Usage

```bash
cap task submit --capability simple_coder --input requirements.md
```

## Spec notes

This capability's `capability.toml` contains no model or provider fields.
The Routing Engine selects the runtime based on `work_profile` and the active `harness.toml` policy.
