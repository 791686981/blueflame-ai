# Repository Guidelines

## 使用中文回答

## Project Structure & Module Organization
- `src/agents/` houses agents (`template_agent`, `design_assistant`) with `agent.py` + `prompt.py`. `langgraph.json` maps graph names (`chat_agent`, `design_assistant`) to `src.agents.template_agent.agent:agent` (adjust when adding new graphs).
- Tools live in `src/tools/`; `registry.py` + `tool_manager.py` register DashScope/StdIO MCP specs and Python callables, while wrappers (e.g., `weather.py`, `web_search.py`) expose tool lists. Shared config/logging sits in `src/common/`, model factories in `src/models/`. Runtime settings/env keys come from `.env`. Dependencies are tracked in `pyproject.toml` and `uv.lock` (Python ≥3.12).

## Build, Test, and Development Commands
- Install: `uv sync` (preferred) or `uv pip install -e .`. Pip fallback: `python -m pip install -e .`.
- Run the template agent once: `uv run python -m src.agents.template_agent.agent` (prints the last message content).
- Dev loop with LangGraph: `uv run langgraph dev chat_agent` using `langgraph.json` and `.env`; switch the graph name if you register another agent.
- No dedicated build; keep deps in `pyproject.toml` and regenerate `uv.lock` with `uv lock` when they change.

## Coding Style & Naming Conventions
- 4-space indent, type hints, and short docstrings; mirror `src/tools/registry.py`. Favor pure functions and early returns.
- Naming: `snake_case` for functions/vars/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants/env keys. Export tool lists in lowercase (`weather`, `web_search`).
- Formatting/linting: follow PEP8/Black/Ruff defaults (88–100 cols). Preferred commands if you add tooling scripts: `uv run ruff check .` and `uv run ruff format .` or `uv run black .`.
- Logging via `logging` configured in `src/common/logging_config.py`; avoid stray `print`.

## Testing Guidelines
- No suite yet. Add `tests/` mirroring `src/` modules; use `pytest` (and `pytest-asyncio` for async code). Run with `uv run pytest`. Mock external MCP/LLM calls; mark slow/network tests.

## Commit & Pull Request Guidelines
- No history yet—start with Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`); keep subjects ≤72 chars.
- PRs: brief summary, bullet key changes, tests run (`uv run pytest` or the agent demo command), linked issues/tasks, and note any new env vars or data files. Screenshots/log snippets only when UX output changes.

## Security & Configuration Notes
- Keep secrets in `.env`; keys referenced in `src/common/config.py` include `DASHSCOPE_API_KEY`, `AMAP_MAPS_API_KEY`, etc. Never commit `.env`; add `.env.example` entries when introducing new keys.
- Register new MCP tools centrally in `src/tools/registry.py`, then wrap them with a thin module exporting tool lists so agents can `import src.tools.<name>` reliably.
