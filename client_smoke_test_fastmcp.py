#!/usr/bin/env python3
"""Bonus checks for the FastMCP-only primitives (resource + prompt).

server.py (hand-rolled) has neither, so these live in a separate file and run
only against server_fastmcp.py (CI's fastmcp track).
"""
import json, os, subprocess, sys

env = dict(os.environ, MCP_WORKSPACE=os.getcwd())
p = subprocess.Popen(
    [sys.executable, "server_fastmcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
)

def send(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()

def request(msg):
    send(msg)
    line = p.stdout.readline().strip()
    print(line)
    return json.loads(line)

try:
    request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "bonus", "version": "0"}}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    res = request({"jsonrpc": "2.0", "id": 2, "method": "resources/read",
                   "params": {"uri": "workspace://files"}})
    prompts = request({"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}})
    pget = request({"jsonrpc": "2.0", "id": 4, "method": "prompts/get",
                    "params": {"name": "explain_word_count", "arguments": {"text": "a b c"}}})
finally:
    p.kill()

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

res_text = res["result"]["contents"][0]["text"]
check("server_fastmcp.py" in res_text, "resource lists workspace files")
prompt_names = {pr["name"] for pr in prompts["result"]["prompts"]}
check("explain_word_count" in prompt_names, "prompt is listed")
msg_text = pget["result"]["messages"][0]["content"]["text"]
check("a b c" in msg_text, "prompt renders its argument")

if failures:
    print("\nFAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("\nOK: FastMCP bonus checks passed (resource + prompt)")
