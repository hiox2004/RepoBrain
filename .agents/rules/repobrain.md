# RepoBrain V2 Agent Operating Rules

When working in this repository with Antigravity or any MCP-enabled coding agent, you MUST strictly adhere to the **5-Phase Chain-of-Thought (CoT)** protocol:

## 1. Mandatory 5-Phase CoT XML Reasoning Protocol

Before invoking tools or editing files, wrap your thinking in these five sequential tags:

```xml
<context_retrieval>
Search the codebase using search_codebase(query, top_k=5, include_episodes=True).
Inspect both the <parent_imports> and <child_body> blocks.
Check if any <past_episodic_fix> matches the current problem or symbol.
</context_retrieval>

<conceptual_grounding>
If unsure about framework semantics, call research_technology(query).
If creating greenfield scaffolding, call search_templates(query).
Cite the exact repository, file, and line ranges to the developer.
</conceptual_grounding>

<diagnostic_hypothesis>
State the exact root cause of the error or requirements gap in <= 40 words.
Formulate the minimal diff required to satisfy tests without modifying assertions.
</diagnostic_hypothesis>

<surgical_patch>
Synthesize unified diff adhering to Guardrails #1 and #2 (byte-safe offsets, outer decorators).
Submit patch via apply_git_patch(patch_str, test_path, task_id).
</surgical_patch>

<verification_verdict>
Inspect PatchAndTestResponse:
- Check exit_code == 0
- Check static_check_passed == True
- If failed on iteration < 3: diagnose filtered_traceback and refine patch.
- If failed on iteration == 3: verify surgical rollback restored pre-task bytes.
</verification_verdict>
```

## 2. Inviolable Guardrails

- **Zero Assertion Weakening:** Never modify `assert` statements in existing test suites just to pass tests.
- **Sanctuary Policy:** Never attempt edits to `*.lock`, `.env`, or `.repobrain/policy.toml`.
- **Bounded Retries:** Never exceed 3 self-healing retry iterations per `task_id`.

