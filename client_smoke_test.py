import json, subprocess, sys
p=subprocess.Popen([sys.executable,"server.py"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
for msg in [{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}},{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}},{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"text":"hello"}}}]:
    p.stdin.write(json.dumps(msg)+"\n"); p.stdin.flush(); print(p.stdout.readline().strip())
p.kill()
