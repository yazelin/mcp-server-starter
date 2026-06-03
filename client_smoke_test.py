#!/usr/bin/env python3
"""Smoke test for the MCP protocol surface shared by both server implementations.

Drives a stdio MCP server through a proper initialize handshake, then exercises
the four tools and the workspace security boundary, asserting the results.
Exits non-zero on any failure so CI can gate on it.

Target server is chosen by MCP_SMOKE_TARGET (default: server.py). The same
assertions pass against both server.py (hand-rolled) and server_fastmcp.py
(FastMCP) because they expose the same tools over the same protocol.
"""
import json, os, subprocess, sys

TARGET = os.getenv("MCP_SMOKE_TARGET", "server.py")
env = dict(os.environ, MCP_WORKSPACE=os.getcwd())
p = subprocess.Popen(
    [sys.executable, TARGET],
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
    init = request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "smoke-test", "version": "0"}}})
    # Required by the MCP handshake: FastMCP won't serve requests without it;
    # the hand-rolled server ignores it (sends nothing back), so don't read a line.
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    listed = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    echo = request({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "echo", "arguments": {"text": "hello"}}})
    wc = request({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                  "params": {"name": "word_count", "arguments": {"text": "the quick brown fox jumps"}}})
    # Security boundary: a path escaping MCP_WORKSPACE must be a clean tool error.
    escape = request({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                      "params": {"name": "read_text_file", "arguments": {"path": "../../etc/passwd"}}})
finally:
    p.kill()

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

names = {t["name"] for t in listed["result"]["tools"]}
check(init["result"]["serverInfo"]["name"].startswith("mcp-server-starter"), "initialize serverInfo.name")
check(names == {"echo", "now", "read_text_file", "word_count"}, f"tools == 4 expected, got {sorted(names)}")
check(echo["result"]["content"][0]["text"] == "hello" and echo["result"]["isError"] is False, "echo returns hello")
check(wc["result"]["content"][0]["text"] == "5" and wc["result"]["isError"] is False, "word_count of 5 words == 5")
check(escape["result"]["isError"] is True, "escape path is rejected (isError true)")
check("escapes workspace" in escape["result"]["content"][0]["text"], "escape error message mentions workspace")

if failures:
    print("\nFAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print(f"\nOK: all 6 checks passed (target={TARGET})")
