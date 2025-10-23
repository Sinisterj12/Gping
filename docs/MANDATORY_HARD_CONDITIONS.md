# Mandatory Hard Conditions

These are the guardrails the automation must respect on every project iteration:

1. The human operator does **not** write or edit code; the AI agent owns scaffolding, implementation, and testing end-to-end.
2. Default to full automation — only request human input when a policy/legal block prevents autonomous action.
3. Always record any unavoidable human follow-up in `HUMAN_TASKS.md` and list data pulls in `HUMAN_RETRIEVAL.md`.
4. Keep runtime artifacts (`data/queue`, `data/logs`, etc.) out of version control unless explicitly requested for analysis.
5. Protect credentials: never embed real store IDs, API keys, or secrets in commits; use placeholders such as `KS-218`.

If a new blocker arises that violates these conditions, pause and document it here before proceeding.
