# Mini-Harness

A minimal coding agent harness for the AISD Harness Engineering tutorial. It
runs an LLM-driven loop with four tools (`list_files`, `read_file`,
`edit_file`, `run_bash`) inside a locked-down Docker sandbox.

## Requirements

- Python 3.12+ (3.14 recommended)
- Docker (the agent runs commands inside a sandboxed container)
- An API key for at least one of the providers in `models.toml`

## Install

```bash
cd harness
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

On macOS, if `python3` is older than 3.12, install a newer one
(`brew install python@3.14`) and use `python3.14 -m venv .venv` instead.

## Run

Set the API key for the model you want to use, then point the harness at a
project directory to work on:

```bash
export LITELLM_API_KEY=...           # or ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
mini-harness /path/to/project
```

Pick a non-default model with `--model`:

```bash
mini-harness /path/to/project --model claude
```

Available aliases (`qwen`, `claude`, `gpt`, `gemini`) and their providers are
defined in [`models.toml`](models.toml).
