#!/usr/bin/env python3
"""Smoke test: spawn server.py over stdio and exercise the JSON-RPC protocol.

Prints every response line (so you can read the real protocol traffic), then
asserts the key invariants. Exits non-zero on any failure so CI can gate on it.
"""
import json, os, subprocess, sys

env = dict(os.environ, MCP_WORKSPACE=os.getcwd())
p = subprocess.Popen(
    [sys.executable, "server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
)

def rpc(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
    line = p.stdout.readline().strip()
    print(line)
    return json.loads(line)

try:
    init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    listed = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    echo = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "echo", "arguments": {"text": "hello"}}})
    wc = rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
              "params": {"name": "word_count", "arguments": {"text": "the quick brown fox jumps"}}})
    # Security boundary: a path escaping MCP_WORKSPACE must be refused as a clean
    # tool error (isError: true), not a transport crash.
    escape = rpc({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                  "params": {"name": "read_text_file", "arguments": {"path": "../../etc/passwd"}}})
finally:
    p.kill()

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

names = {t["name"] for t in listed["result"]["tools"]}
check(init["result"]["serverInfo"]["name"] == "mcp-server-starter", "initialize serverInfo.name")
check(names == {"echo", "now", "read_text_file", "word_count"}, f"tools/list names == 4 expected, got {sorted(names)}")
check(echo["result"]["content"][0]["text"] == "hello" and echo["result"]["isError"] is False, "echo returns hello")
check(wc["result"]["content"][0]["text"] == "5" and wc["result"]["isError"] is False, "word_count of 5 words == 5")
check(escape["result"]["isError"] is True, "escape path is rejected (isError true)")
check("escapes workspace" in escape["result"]["content"][0]["text"], "escape path error message mentions workspace")

if failures:
    print("\nFAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("\nOK: all 6 checks passed")
