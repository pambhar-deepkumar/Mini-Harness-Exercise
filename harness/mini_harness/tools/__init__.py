from ..sandbox import Sandbox
from . import bash_tools, file_tools, plan_tools

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
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": (
                "Search recursively for a text pattern across files in the workspace "
                "using grep. Returns matching lines in the format file:line:match. "
                "Use this to find TODOs, function definitions, string occurrences, etc. "
                "without running a shell command."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regular expression or literal string to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory or file path relative to /workspace to search in. "
                            "Use '.' to search the entire workspace."
                        ),
                    },
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan",
            "description": (
                "Store or update the agent's current plan as a list of tasks. "
                "Call this early in a multi-step task to outline what you intend to do, "
                "then call it again as steps are completed to flip the 'done' flag. "
                "The plan is injected into the system prompt on every subsequent turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Ordered list of plan steps.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "Short description of the step.",
                                },
                                "done": {
                                    "type": "boolean",
                                    "description": "True if the step has been completed.",
                                },
                            },
                            "required": ["task"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
]


def dispatch(name: str, tool_input: dict, sandbox: Sandbox, state: dict | None = None) -> str:
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

    if name == "grep_files":
        return bash_tools.grep_files(tool_input["pattern"], tool_input["path"], sandbox)

    if name == "update_plan":
        return plan_tools.update_plan(tool_input["items"], state if state is not None else {})

    return f"Unknown tool: {name}"
