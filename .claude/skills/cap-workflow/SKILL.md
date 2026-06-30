---
name: cap-workflow
description: Run a full Capability Harness task from submission to approval using the cap MCP tools
allowed-tools: mcp__capability-harness__*
---

You have access to the Capability Harness MCP tools. Use them to orchestrate the full task lifecycle:

1. **Discover** available capabilities with `capability_list`
2. **Submit** a task with `task_submit(capability=..., input_file=...)`
3. **Poll** `task_status(task_id)` until state reaches "review" or "validation"
4. **Inspect** the output with `artifact_get(task_id, "patch.diff")`
5. **Approve** with `task_approve(task_id)` or **reject** with `task_reject(task_id, reason=...)`
6. **Report** metrics with `benchmark_report()`

**Rules:**
- Always show the user the `patch.diff` artifact before approving — never approve blindly
- If a task fails, check `task_status` for the error message before retrying
- Use `model_list` to show what local models are available; suggest `model_pull` if none are downloaded
- The framework owns process — you are an operator of it, not its replacement
