# GPing Project Conventions

## Environment & Dependencies
- **Initialization:** For new projects, `uv init` is used. The virtual environment is created automatically the first time a command like `uv run` is executed (e.g., `uv run python hello.py`).
- **Adding Dependencies:** Use `uv add <package-name>`. Do not edit `pyproject.toml` or `uv.lock` manually.
- **Removing Dependencies:** Use `uv remove <package-name>`.

## Running the Application
- The correct command to run the development version is: `uv run ping_tool.py`

## Git Workflow
- Do not push to the remote repository. Only fetch or pull.

## Logging and Notes
- **Session Log:** After every action that modifies the project, you must update `AI_Session_log.md`. The log entry must describe the exact action taken, including file paths and a clear rationale, to ensure changes can be easily reversed if needed.
- **GistPad:** Be aware that notes and snippets may be managed using GistPad.

## Interaction Protocol
- **Proposing Actions:** When a task requires multiple steps or significant changes, I will first propose a clear, concise plan.
- **Discussion & Refinement:** You are encouraged to ask questions, suggest modifications, or request clarification on the proposed plan. I will engage in this discussion until the plan is satisfactory.
- **Execution:** Only after you explicitly approve the plan will I proceed with executing the actions using my tools. Tool calls (which require your confirmation) will only be initiated at this stage.