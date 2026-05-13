import json
import os
import tomllib
from pathlib import Path

import litellm

from . import tools
from .sandbox import Sandbox
from .tools.plan_tools import format_plan

CONFIG_PATH = Path(__file__).resolve().parent.parent / "models.toml"

_BASE_SYSTEM_PROMPT = (
    "You are a coding assistant operating inside a sandboxed Linux container. "
    "The user's project is bind-mounted at /workspace. "
    "Explore before editing, make small focused changes, and briefly summarize what you did."
)

# Conversation compaction settings
COMPACT_AFTER = 30  # compact when the messages list exceeds this length
KEEP_RECENT = 10    # always keep the last N messages untouched


def _build_system_message(state: dict) -> str:
    content = _BASE_SYSTEM_PROMPT
    plan = state.get("plan")
    if plan:
        content += "\n\n# Current plan\n" + format_plan(plan)
    return content


def load_config(model_alias: str | None = None) -> dict:
    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    alias = (
        model_alias
        or os.environ.get("MINI_HARNESS_MODEL")
        or config.get("default")
    )
    models = config.get("models", {})
    if not alias or alias not in models:
        available = ", ".join(sorted(models)) or "(none)"
        raise SystemExit(f"Unknown model alias '{alias}'. Available: {available}")

    return {"alias": alias, **models[alias]}


def _completion_kwargs(cfg: dict, messages: list[dict]) -> dict:
    kwargs: dict = {
        "model": cfg["model"],
        "messages": messages,
        "tools": tools.TOOL_SCHEMAS,
        "max_tokens": cfg.get("max_tokens", 4096),
    }
    if cfg.get("api_base"):
        kwargs["api_base"] = cfg["api_base"]
    if env_var := cfg.get("api_key_env"):
        api_key = os.environ.get(env_var)
        if not api_key:
            raise SystemExit(
                f"Environment variable {env_var} is not set "
                f"(required by model '{cfg['alias']}')."
            )
        kwargs["api_key"] = api_key
    return kwargs


def _compact(messages: list[dict], cfg: dict) -> None:
    """Summarize older turns in-place, preserving messages[0] (system) and the last KEEP_RECENT messages."""
    # messages[0] is always the system message; we only compact the slice between it and KEEP_RECENT
    # Layout: [system, ...older..., ...recent(KEEP_RECENT)...]
    older_slice = messages[1 : len(messages) - KEEP_RECENT]
    if not older_slice:
        return

    # Find a safe cut point: prefer ending just before a user message so we
    # never split a tool call from its result.
    cut = len(older_slice)
    for i in range(len(older_slice) - 1, 0, -1):
        if older_slice[i].get("role") == "user":
            cut = i
            break

    to_summarize = older_slice[:cut]
    if not to_summarize:
        return

    summary_prompt = [
        {
            "role": "system",
            "content": (
                "You are a concise summarizer. Summarize the following conversation "
                "turns into a single paragraph that preserves key decisions, files "
                "changed, commands run, and their outcomes. Be brief."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(to_summarize, default=str),
        },
    ]

    summary_kwargs: dict = {
        "model": cfg["model"],
        "messages": summary_prompt,
        "max_tokens": 512,
    }
    if cfg.get("api_base"):
        summary_kwargs["api_base"] = cfg["api_base"]
    if env_var := cfg.get("api_key_env"):
        api_key = os.environ.get(env_var, "")
        if api_key:
            summary_kwargs["api_key"] = api_key

    try:
        response = litellm.completion(**summary_kwargs)
        summary_text = response.choices[0].message.content or "(summary unavailable)"
    except Exception as exc:  # noqa: BLE001
        summary_text = f"(summary failed: {exc})"

    synthetic = {
        "role": "user",
        "content": f"[Summary of earlier turns]\n{summary_text}",
    }

    # Replace the older slice with the single synthetic message
    del messages[1 : 1 + cut]
    messages.insert(1, synthetic)


def run(sandbox: Sandbox, model_alias: str | None = None) -> None:
    cfg = load_config(model_alias)
    state: dict = {}
    messages: list[dict] = [{"role": "system", "content": _build_system_message(state)}]

    print(f"Mini-Harness ready. Model: {cfg['alias']} ({cfg['model']}). Ctrl+D to exit.")

    while True:
        try:
            user_input = input("\n> ").strip()
        except EOFError:
            print()
            return

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        _run_turn(messages, sandbox, cfg, state)


def _run_turn(messages: list[dict], sandbox: Sandbox, cfg: dict, state: dict) -> None:
    while True:
        # Update system message with current plan before each LLM call
        messages[0] = {"role": "system", "content": _build_system_message(state)}

        # Compact if the conversation has grown too long
        if len(messages) > COMPACT_AFTER:
            _compact(messages, cfg)

        response = litellm.completion(**_completion_kwargs(cfg, messages))
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            print(message.content)

        tool_calls = message.tool_calls or []
        if not tool_calls:
            return

        for call in tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            preview = json.dumps(args)[:80]
            print(f"  [tool] {name}({preview})")
            output = tools.dispatch(name, args, sandbox, state)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": output,
            })
