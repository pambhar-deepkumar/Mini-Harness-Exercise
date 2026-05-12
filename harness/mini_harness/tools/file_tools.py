from ..sandbox import Sandbox


def list_files(path: str, sandbox: Sandbox) -> str:
    exit_code, out, err = sandbox.exec(["ls", "-la", "--", path])
    if exit_code != 0:
        return f"Error: {err.strip()}"
    return out


def read_file(path: str, sandbox: Sandbox) -> str:
    exit_code, out, err = sandbox.exec(["cat", "--", path])
    if exit_code != 0:
        return f"Error: {err.strip()}"
    return out


def edit_file(path: str, old_str: str, new_str: str, sandbox: Sandbox) -> str:
    if old_str == "":
        return _create_file(path, new_str, sandbox)
    return _replace_in_file(path, old_str, new_str, sandbox)


def _create_file(path: str, contents: str, sandbox: Sandbox) -> str:
    already_exists, _, _ = sandbox.exec(["test", "-e", path])
    if already_exists == 0:
        return f"Error: {path} already exists. Pass a non-empty old_str to edit it."

    write_exit_code, write_err = sandbox.write_file(path, contents)
    if write_exit_code != 0:
        return f"Error writing {path}: {write_err.strip()}"
    return f"Created {path} ({len(contents)} bytes)."


def _replace_in_file(path: str, old_str: str, new_str: str, sandbox: Sandbox) -> str:
    exit_code, content, err = sandbox.exec(["cat", "--", path])
    if exit_code != 0:
        return f"Error reading {path}: {err.strip()}"

    match_count = content.count(old_str)
    if match_count == 0:
        return f"Error: old_str not found in {path}."
    if match_count > 1:
        return (
            f"Error: old_str matches {match_count} times in {path}; "
            "make it unique by including more surrounding context."
        )

    updated_content = content.replace(old_str, new_str, 1)
    write_exit_code, write_err = sandbox.write_file(path, updated_content)
    if write_exit_code != 0:
        return f"Error writing {path}: {write_err.strip()}"
    return f"Edited {path}."
