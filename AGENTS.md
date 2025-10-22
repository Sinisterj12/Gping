# Repository Guidelines

## Project Structure & Module Organization
Core agent code lives in `gping_next/`, with runtime orchestration in `core_runtime.py` and typed payloads in `schemas.py`. Align new services with this layout and expose entry points via `__main__.py`. Tests reside under `tests/` and mirror module names. Field helpers live in `scripts/` (`install.ps1`, `unlock.ps1`, `sendnow.ps1`, `uninstall.ps1`), while `dashboard/apps_script/` contains Google Apps Script stubs referenced by telemetry uploads. Runtime artefacts (`data/logs`, `data/queue`, `data/ui`) stay untracked for local validation.

## Build, Test, and Development Commands
Use `uv sync` to install or refresh the Python 3.11 environment. `uv run python -m gping_next --once` executes a single probe cycle and writes CSV/JSONL logs under `data/logs/`. Drop a `SENDNOW` file or run `./scripts/sendnow.ps1` before re-running to force telemetry uploads into `data/queue/sent/`. `uv run python -m gping_next` keeps the agent alive for long trials. Validate any change with `uv run pytest`, and add focused tests under `tests/` when behaviour shifts.

## Coding Style & Naming Conventions
Follow the existing 4-space indentation, explicit type hints, and dataclasses with `slots=True` for payloads. Module and function names stay snake_case; classes use PascalCase (`GPingNextAgent`, `TelemetryManager`). Keep public functions side-effect free unless clearly labelled, and prefer the `pathlib` and `datetime` utilities already in use. Configuration defaults belong in `config.py`, and new triggers should register through `TaskRegistry` to remain discoverable.

## Testing Guidelines
Extend the pytest suite by mirroring current patterns (`tests/test_logger.py`, `tests/test_policy.py`). Favour unit fixtures from `tests/conftest.py` and assert on structured payloads instead of timing-based expectations. Before shipping, run `uv run python -m gping_next --once` to confirm CSV/JSONL output and queue rollover, then execute `uv run pytest`. Aim to cover error paths—unreachable targets, unlock tokens, telemetry retries—for every new feature.

## Commit & Pull Request Guidelines
History shows concise subject lines such as “Polish GPING NEXT docs and telemetry coverage”. Keep commits focused, formatted as imperative phrases under ~72 characters, and include context in the body when behaviour changes. Pull requests should outline motivation, the commands you ran (`uv run pytest`, smoke run logs), and any dashboard or Apps Script updates. Attach relevant log snippets or config diffs whenever telemetry or data formats move.

## Field Operations Notes
Never commit real store IDs or credentials; use `KS-218` style placeholders. After local smoke tests, clean the `data/queue/` directory so binary artefacts do not slip into PRs. Coordinate with operations before modifying PowerShell installers, and document any Windows permission changes in `docs/OPERATIONS.md`.
