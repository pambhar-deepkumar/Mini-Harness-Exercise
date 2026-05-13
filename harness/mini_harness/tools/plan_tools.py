def format_plan(items: list[dict]) -> str:
    lines = []
    for item in items:
        marker = "x" if item.get("done") else " "
        lines.append(f"- [{marker}] {item['task']}")
    return "\n".join(lines)


def update_plan(items: list[dict], state: dict) -> str:
    normalized = [
        {"task": i.get("task", ""), "done": bool(i.get("done", False))}
        for i in items
    ]
    state["plan"] = normalized
    return "Plan updated:\n" + format_plan(normalized)
