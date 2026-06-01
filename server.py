#!/usr/bin/env python3
import json, os, sys
from datetime import datetime
from pathlib import Path
WORKSPACE=Path(os.getenv("MCP_WORKSPACE",os.getcwd())).resolve()
def send(o): sys.stdout.write(json.dumps(o,ensure_ascii=False)+"\n"); sys.stdout.flush()
def tools(): return [{"name":"echo","description":"Echo text","inputSchema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}},{"name":"now","description":"Current local time","inputSchema":{"type":"object","properties":{}}},{"name":"read_text_file","description":"Read UTF-8 text under MCP_WORKSPACE","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}]
def safe(rel):
    p=(WORKSPACE/rel).resolve()
    if not str(p).startswith(str(WORKSPACE)): raise ValueError("Path escapes workspace")
    return p
def call(name,args):
    args=args or {}
    if name=="echo": return args.get("text","")
    if name=="now": return datetime.now().astimezone().isoformat(timespec="seconds")
    if name=="read_text_file": return safe(args["path"]).read_text(encoding="utf-8")[:20000]
    raise ValueError("Unknown tool: "+str(name))
def handle(req):
    mid=req.get("id"); m=req.get("method")
    try:
        if m=="initialize": res={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"mcp-server-starter","version":"0.1.0"}}
        elif m=="tools/list": res={"tools":tools()}
        elif m=="tools/call":
            p=req.get("params",{}); res={"content":[{"type":"text","text":call(p.get("name"),p.get("arguments",{}))}]}
        elif m=="notifications/initialized": return None
        else: raise ValueError("Unsupported method: "+str(m))
        return {"jsonrpc":"2.0","id":mid,"result":res}
    except Exception as e: return {"jsonrpc":"2.0","id":mid,"error":{"code":-32000,"message":str(e)}}
for line in sys.stdin:
    if line.strip():
        r=handle(json.loads(line))
        if r is not None: send(r)
