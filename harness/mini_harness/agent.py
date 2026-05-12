import json
import os
import tomllib
from pathlib import Path

import litellm

from . import tools
from .sandbox import Sandbox

CONFIG_PATH = Path(__file__).resolve().parent.parent / "models.toml"

SYSTEM_PROMPT = (
    "You are a coding assistant operating inside a sandboxed Linux container. "
    "The user's project is bind-mounted at /workspace. "
    "Explore before editing, make small focused changes, and briefly summarize what you did."
)


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


def run(sandbox: Sandbox, model_alias: str | None = None) -> None:
    cfg = load_config(model_alias)
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

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
        _run_turn(messages, sandbox, cfg)


def _run_turn(messages: list[dict], sandbox: Sandbox, cfg: dict) -> None:
    while True:
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
            output = tools.dispatch(name, args, sandbox)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": output,
            })
