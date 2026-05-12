# Mini-Harness Tasks

## Task 1: Add a `grep_files` tool

Add a `grep_files(pattern, path)` tool to the Mini-Harness so the agent can
search across the workspace without having to fall back to `run_bash`.

### Requirements

- Register the tool in `TOOL_SCHEMAS` (in `harness/mini_harness/tools/__init__.py`)
  and wire it into `dispatch` so the model can call it directly.
- The implementation should run `grep -rn` (or an equivalent recursive search)
  inside the sandbox at the given `path`.
- Return the matches as a plain string (file:line:match per line is fine).
- The model should be able to use it without any prompt-engineering tweaks —
  the schema description must be clear enough on its own.

### Done when

- `find every TODO in the project` triggers a `grep_files` call instead of a
  `run_bash` call, and the agent reports back the hidden TODOs planted in the
  `todo-app/` codebase.

## Task 2: Add an `update_plan` tool with state-backed prompt injection

Give the agent a simple planning tool so it can keep a running to-do list of
its own work and always sees its current plan.

### Requirements

- Add an `update_plan(items)` tool where `items` is a list of `{task, done}`
  entries. The tool normalizes the list and stores it in a shared `state` dict
  owned by the harness (not in the messages list).
- Register `update_plan` in `TOOL_SCHEMAS` and wire it into `dispatch`. The
  dispatcher (or agent) needs access to `state` in addition to the sandbox.
- Build the system message dynamically each turn: start from the base prompt,
  then append a `# Current plan` section rendered from `state["plan"]` if a
  plan exists. Replace the static `SYSTEM_PROMPT` constant usage in
  `agent.py` with a `_build_system_message(state)` helper that runs on every
  iteration.
- The tool should return a human-readable confirmation (e.g. the formatted
  plan) so the model gets feedback in the tool result too.

### Example shape

```python
def update_plan(items: list[dict], state: dict) -> str:
    normalized = [
        {"task": i.get("task", ""), "done": bool(i.get("done", False))}
        for i in items
    ]
    state["plan"] = normalized
    return "Plan updated:\n" + format_plan(normalized)
```

### Done when

- Asking the agent to do a multi-step task (e.g. "add a `priority` field to
  todos end-to-end: model, DB, API, and UI") causes it to call `update_plan`
  early, and subsequent turns show the plan reflected in the system prompt
  with `done` flags flipping over time.

## Task 3: Add conversation compaction

Long sessions can fill up the model's context window. Add a compaction step
that summarizes older turns into a single message so the conversation stays
compact while preserving the most recent context.

### Requirements

- Trigger compaction when `len(messages)` exceeds a threshold (e.g.
  `COMPACT_AFTER = 30`). Always keep the last N messages untouched (e.g.
  `KEEP_RECENT = 10`).
- **Never split a tool call from its tool result.** Find a safe cut point —
  try to split at user messages so that tool calls and results are not divided.
- Summarize the older slice via a separate LiteLLM call
- Replace the older slice in-place with a single synthetic user message that
  starts with something like `[Summary of earlier turns]` so the model knows
  it's reading a recap, not a real user turn.
- The system message at `messages[0]` stays put — only the conversation tail
  between it and `KEEP_RECENT` is compacted.

### Done when

- Running a long session (set `COMPACT_AFTER` low, e.g. 8, while testing)
  shows a `[Summary of earlier turns]` message replacing older turns once
  the threshold is crossed, the agent keeps working without errors.

## Task 4: Give the sandbox a real Python toolchain

Right now the sandbox image is `alpine:3.23` with `git` and nothing else, so
the agent cannot actually run the code it writes. Extend the container so
the agent can verify its own work end-to-end — running tests, type checks...

### Requirements

- Update `harness/container/Dockerfile` to install Python 3.12+ and the tools
  the agent will need to validate work on the todo-app:
  - `pytest` (and `pytest-asyncio` / `httpx` for FastAPI tests)
  - `mypy`
  - `fastapi`, `uvicorn`, `pydantic`
  - anything else the todo-app's `requirements.txt` needs at import time
- Pre-install the Python dependencies at image build time. The sandbox runs
  with `--network none` (see `harness/mini_harness/sandbox.py`), so `pip
  install` at runtime will fail — everything must be baked into the image.
- Bump the `IMAGE_TAG` in `sandbox.py` (e.g. `mini-harness:py312`) so
  existing cached images get rebuilt instead of silently reused.

### Done when

- Asking the agent "write a pytest for `GET /todos` and run it" inside the
  todo-app workspace results in a `run_bash` call to `pytest` that actually
  executes and reports pass/fail


