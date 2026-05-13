from ..sandbox import Sandbox


def run_bash(command: str, sandbox: Sandbox) -> str:
    exit_code, out, err = sandbox.exec(["sh", "-c", command])

    output_sections = []
    if out:
        output_sections.append(out)
    if err:
        output_sections.append(f"[stderr]\n{err}")
    if exit_code != 0:
        output_sections.append(f"[exit code: {exit_code}]")

    if not output_sections:
        return "(no output)"
    return "\n".join(output_sections)


def grep_files(pattern: str, path: str, sandbox: Sandbox) -> str:
    exit_code, out, err = sandbox.exec(
        ["grep", "-rn", pattern, "--", path]
    )
    if exit_code == 0:
        return out if out else "(no matches)"
    if exit_code == 1:
        # grep exits 1 when no matches found
        return "(no matches)"
    return f"Error: {err.strip()}"
