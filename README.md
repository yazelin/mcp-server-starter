# MCP Server Starter

Learn MCP by building a tiny dependency-light tool server.

## Who this is for

Developers who want to connect Claude/Cursor/agents to their own tools.

## Features

- JSON-RPC stdio server
- Example tools: echo, now, read_text_file
- Workspace safety boundary
- Smoke test client

## Quick start

```bash
git clone https://github.com/yazelin/mcp-server-starter.git
cd mcp-server-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if present
```

See the source files and `.env.example` for the minimal runnable path.

## Learn / get help

This repo is also a CTA page for workshops and consulting:

- GitHub Pages: https://yazelin.github.io/mcp-server-starter/
- Contact: yaze.lin.j303@gmail.com

## License

MIT
