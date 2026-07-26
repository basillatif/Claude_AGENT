"""Tool implementations and their JSON schema definitions for the agent.

To add a new tool:
1. Write a plain function that takes the tool's arguments and returns a string.
2. Write a matching JSON schema dict describing its name/description/inputs.
3. Register both in TOOLS and TOOL_SCHEMAS at the bottom of this file.
"""

import ast
import operator
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# calculator
# ---------------------------------------------------------------------------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _eval_node(node.left), _eval_node(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"unsupported expression node: {ast.dump(node)}")


def calculator(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression (no eval())."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as exc:
        return f"Error: invalid expression ({exc})"


CALCULATOR_SCHEMA = {
    "name": "calculator",
    "description": (
        "Evaluate a basic arithmetic expression (+, -, *, /, //, %, **, parentheses, "
        "unary minus). Returns the numeric result as a string, or an 'Error: ...' "
        "message if the expression is invalid."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The arithmetic expression to evaluate, e.g. '2 + 2 * (3 - 1)'",
            }
        },
        "required": ["expression"],
    },
}


# ---------------------------------------------------------------------------
# read_file / write_file — sandboxed to ./workspace
# ---------------------------------------------------------------------------


def _resolve_in_workspace(path: str) -> Path:
    """Resolve `path` relative to the workspace dir; reject any escape attempt."""
    workspace_resolved = WORKSPACE_DIR.resolve()
    candidate = (workspace_resolved / path).resolve()
    if candidate != workspace_resolved and workspace_resolved not in candidate.parents:
        raise ValueError(f"path '{path}' is outside the sandboxed workspace directory")
    return candidate


def read_file(path: str) -> str:
    """Read a file's contents from the sandboxed ./workspace directory."""
    try:
        target = _resolve_in_workspace(path)
    except ValueError as exc:
        return f"Error: {exc}"
    if not target.is_file():
        return f"Error: '{path}' does not exist or is not a file"
    return target.read_text()


def write_file(path: str, content: str) -> str:
    """Write content to a file in the sandboxed ./workspace directory."""
    try:
        target = _resolve_in_workspace(path)
    except ValueError as exc:
        return f"Error: {exc}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Wrote {len(content)} characters to '{path}'"


READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": (
        "Read the contents of a file inside the sandboxed ./workspace directory. "
        "Paths outside the workspace are rejected."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the workspace directory, e.g. 'notes.txt'",
            }
        },
        "required": ["path"],
    },
}

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": (
        "Write text content to a file inside the sandboxed ./workspace directory, "
        "creating it (and parent directories) if needed. Paths outside the "
        "workspace are rejected."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the workspace directory, e.g. 'notes.txt'",
            },
            "content": {
                "type": "string",
                "description": "The text content to write to the file.",
            },
        },
        "required": ["path", "content"],
    },
}


# ---------------------------------------------------------------------------
# web_search — stubbed for now
# ---------------------------------------------------------------------------


def web_search(query: str) -> str:
    """Stub web search — returns a fixed fake result until a real search API is wired up."""
    return (
        f"[stubbed search result for '{query}']\n"
        "Title: Example Result\n"
        "URL: https://example.com/\n"
        "Snippet: This is a placeholder result. Replace tools.py:web_search() "
        "with a real search API call when you're ready."
    )


WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": (
        "Search the web for information relevant to a query. Currently stubbed "
        "and always returns the same fake result — replace with a real search "
        "API integration later."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"],
    },
}


# ---------------------------------------------------------------------------
# ask_user — real stdin round-trip
# ---------------------------------------------------------------------------


def ask_user(question: str) -> str:
    """Print a question to the user and read their typed response from stdin."""
    print(f"\n[Claude asks]: {question}")
    return input("> ")


ASK_USER_SCHEMA = {
    "name": "ask_user",
    "description": (
        "Ask the human user a question and wait for their typed response. Use "
        "this when you need clarification, a decision, or information only the "
        "user can provide."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question to ask the user"}
        },
        "required": ["question"],
    },
}


# ---------------------------------------------------------------------------
# Registry — add new tools here
# ---------------------------------------------------------------------------

TOOLS = {
    "calculator": calculator,
    "read_file": read_file,
    "write_file": write_file,
    "web_search": web_search,
    "ask_user": ask_user,
}

TOOL_SCHEMAS = [
    CALCULATOR_SCHEMA,
    READ_FILE_SCHEMA,
    WRITE_FILE_SCHEMA,
    WEB_SEARCH_SCHEMA,
    ASK_USER_SCHEMA,
]
