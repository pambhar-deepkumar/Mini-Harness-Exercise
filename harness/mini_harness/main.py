import argparse
import sys
from pathlib import Path

from . import agent
from .sandbox import Sandbox


def main() -> int:
    parser = argparse.ArgumentParser(prog="mini-harness")
    parser.add_argument("project_path", type=Path, help="Project directory to mount as /workspace")
    parser.add_argument(
        "--model",
        help="Model alias from models.toml (e.g. sonnet, qwen, claude, gpt, gemini)",
    )
    args = parser.parse_args()

    workspace = args.project_path.expanduser()
    if not workspace.is_dir():
        print(f"Error: {workspace} is not a directory.", file=sys.stderr)
        return 1

    # Per-model API keys are validated by agent.load_config / _completion_kwargs.
    with Sandbox(workspace) as sandbox:
        agent.run(sandbox, model_alias=args.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
