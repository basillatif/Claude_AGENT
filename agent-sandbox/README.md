# agent-sandbox

A small, dependency-light sandbox for learning how LLM agent loops actually
work — no framework, no magic. Good for experimenting yourself or walking
students through the internals of tool use.

## How it works

1. `main.py` reads a task (CLI arg or interactive prompt) and calls `run_agent()`.
2. `agent.py` runs the loop: send messages to Claude → check for `tool_use`
   blocks in the response → execute the matching tool → send the
   `tool_result` back → repeat until Claude replies with plain text (or
   `--max-turns` is hit, default 10).
3. `tools.py` holds every tool as a plain Python function plus a JSON schema
   Claude uses to know the tool exists and how to call it.

Every tool call and its result is printed to the console as it happens, so
you can watch Claude's reasoning and tool sequencing unfold in real time.

## Setup

```bash
cd agent-sandbox
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set ANTHROPIC_API_KEY
```

## Run it

```bash
python main.py "What's 47 * 89, and then write the answer to a file called result.txt?"

# or interactively:
python main.py

# raise the turn cap for a longer task:
python main.py "some multi-step task" --max-turns 20
```

Files the agent reads/writes always live under `./workspace/` — `read_file`
and `write_file` resolve every path relative to that directory and reject
anything that tries to escape it (`../../etc/passwd`, absolute paths, etc.).

## Tools included

| Tool          | What it does                                                             |
|---------------|---------------------------------------------------------------------------|
| `calculator`  | Evaluates basic arithmetic via a whitelisted AST walk (no `eval()`).       |
| `read_file`   | Reads a file from `./workspace/`.                                         |
| `write_file`  | Writes a file to `./workspace/`.                                          |
| `web_search`  | **Stubbed** — always returns the same fake result. Wire up a real API later. |
| `ask_user`    | Prints a question and reads a real answer from stdin.                     |

If a tool raises an exception, `agent.py` catches it and feeds Claude an
error message as the tool result (`is_error: true`) instead of crashing —
this is a good thing to point out to students, since you can watch Claude
try a different approach after a tool fails.

## Adding a new tool

1. Write a function in `tools.py` that takes the arguments and returns a string.
2. Write a JSON schema dict (`name`, `description`, `input_schema`) describing it.
3. Add both to the `TOOLS` dict and `TOOL_SCHEMAS` list at the bottom of `tools.py`.

That's it — the loop in `agent.py` dispatches by name automatically.

## Phase 2 idea: swap a tool for a real MCP server

Once this is running, a natural next step is replacing one of these
hand-written tools (`web_search` is the obvious candidate) with a real
connection to an MCP (Model Context Protocol) server instead of a
plain Python function — letting Claude call tools exposed by an external
server rather than ones defined inline in `tools.py`. That's a good
follow-up exercise once students are comfortable with the manual loop here.
