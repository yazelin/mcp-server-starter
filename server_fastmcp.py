#!/usr/bin/env python3
"""FastMCP version of the starter server.

Same four tools and the same MCP_WORKSPACE security boundary as server.py, but
written with FastMCP instead of hand-rolled JSON-RPC. Requires the `fastmcp`
extra: `uv sync --extra fastmcp`.
"""
import os
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

WORKSPACE = Path(os.getenv("MCP_WORKSPACE", os.getcwd())).resolve()
mcp = FastMCP("mcp-server-starter-fastmcp")


def safe(rel: str) -> Path:
    """Resolve rel under WORKSPACE, refusing any path that escapes it.

    Identical logic to server.py: .resolve() flattens .. / symlinks / absolute
    paths, then we check the real path stays inside WORKSPACE. FastMCP gives you
    the protocol for free — but this security boundary is still yours to write.
    """
    p = (WORKSPACE / rel).resolve()
    if WORKSPACE != p and WORKSPACE not in p.parents:
        raise ValueError("Path escapes workspace")
    return p


@mcp.tool
def echo(text: str) -> str:
    """Echo text"""
    return text


@mcp.tool
def now() -> str:
    """Current local time"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@mcp.tool
def word_count(text: str) -> str:
    """Count whitespace-separated words in text"""
    return str(len(text.split()))


@mcp.tool
def read_text_file(path: str) -> str:
    """Read UTF-8 text under MCP_WORKSPACE"""
    return safe(path).read_text(encoding="utf-8")[:20000]


@mcp.resource("workspace://files")
def workspace_files() -> str:
    """List the files under MCP_WORKSPACE (read-only context).

    A resource is application/user-provided context addressed by URI — the
    counterpart to the read_text_file tool, which the model calls itself.
    """
    return "\n".join(sorted(p.name for p in WORKSPACE.iterdir()))


@mcp.prompt
def explain_word_count(text: str) -> str:
    """Awareness-only example of the third MCP primitive: a reusable prompt.

    In a minimal file/utility server a prompt is contrived — this exists so you
    can see what a prompt looks like, not because it earns its keep here.
    """
    return f"Count the words in this text and explain your reasoning step by step:\n\n{text}"


def main() -> None:
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
