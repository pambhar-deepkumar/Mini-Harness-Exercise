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
