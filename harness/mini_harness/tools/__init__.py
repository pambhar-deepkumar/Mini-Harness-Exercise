from ..sandbox import Sandbox
from . import bash_tools, file_tools

# OpenAI-style tool schemas. LiteLLM accepts this format for every provider
# (Anthropic, OpenAI, Gemini, ...) and translates internally where needed.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List files and directories at the given path inside the workspace. "
                "Use '.' for the workspace root."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to /workspace.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to /workspace.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Edit a file by replacing old_str with new_str. old_str must match "
                "exactly once in the file. To create a new file, pass an empty old_str "
                "and the desired contents as new_str."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to /workspace.",
                    },
                    "old_str": {
                        "type": "string",
                        "description": "Exact text to replace, or empty string to create a new file.",
                    },
                    "new_str": {
                        "type": "string",
                        "description": "Replacement text (or full contents when creating a file).",
                    },
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Run a shell command inside the workspace and return its combined output. "
                "Use this for builds, tests, package installs, git, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    },
                },
                "required": ["command"],
            },
        },
    },
]


def dispatch(name: str, tool_input: dict, sandbox: Sandbox) -> str:
    if name == "list_files":
        return file_tools.list_files(tool_input["path"], sandbox)

    if name == "read_file":
        return file_tools.read_file(tool_input["path"], sandbox)

    if name == "edit_file":
        return file_tools.edit_file(
            tool_input["path"],
            tool_input["old_str"],
            tool_input["new_str"],
            sandbox,
        )

    if name == "run_bash":
        return bash_tools.run_bash(tool_input["command"], sandbox)

    return f"Unknown tool: {name}"
