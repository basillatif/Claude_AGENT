"""Core agent loop.

Sends messages to Claude, checks the response for tool_use blocks, executes
the corresponding tool, feeds the tool_result back in, and repeats until
Claude returns a final text-only response (or max_turns is hit).
"""

import anthropic

from tools import TOOLS, TOOL_SCHEMAS

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096


def run_agent(task: str, max_turns: int = 10) -> str:
    """Run the agent loop on a single task. Returns Claude's final text response."""
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task}]

    for turn in range(1, max_turns + 1):
        print(f"\n--- turn {turn}/{max_turns} ---")

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"[claude] {block.text.strip()}")

        if response.stop_reason != "tool_use":
            return _final_text(response)

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            content, is_error = _execute_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return f"[agent-sandbox] Stopped after reaching max_turns={max_turns} without a final answer."


def _final_text(response) -> str:
    texts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(texts) if texts else "(no text response)"


def _execute_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run a tool, logging the call and result. Never raises — errors become
    tool_result content with is_error=True so Claude can see and recover."""
    print(f"[tool call] {name}({tool_input})")

    tool_fn = TOOLS.get(name)
    if tool_fn is None:
        error_msg = f"Error: unknown tool '{name}'"
        print(f"[tool result] {error_msg}")
        return error_msg, True

    try:
        result = tool_fn(**tool_input)
        print(f"[tool result] {result}")
        return str(result), False
    except Exception as exc:
        error_msg = f"Error executing '{name}': {exc}"
        print(f"[tool result] {error_msg}")
        return error_msg, True
