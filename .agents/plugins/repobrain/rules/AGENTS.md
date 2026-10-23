# RepoBrain Plugin Rules

When working with RepoBrain tools in Antigravity, Claude Code, or Codex, enforce the 5-Phase CoT:

1. `<context_retrieval>`: Call `search_codebase` (include_episodes=True) or `get_blast_radius`.
2. `<conceptual_grounding>`: Call `research_technology` or `search_templates` if uncertain.
3. `<diagnostic_hypothesis>`: Identify minimal changes needed (< 40 words).
4. `<surgical_patch>`: Apply unified diff via `apply_git_patch`.
5. `<verification_verdict>`: Verify static checks and test results.

