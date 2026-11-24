"""Minimal JSON-RPC client for the Databricks-managed system.ai.sandbox MCP service.

Usage:
  python sandbox_mcp.py list
  python sandbox_mcp.py call <tool_name> '<json arguments>'
"""
import json
import sys

import requests
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
URL = f"{w.config.host.rstrip('/')}/ai-gateway/mcp-services/system.ai.sandbox"
_id = 0


def _headers(session_id=None):
    h = {**w.config.authenticate(), "Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    if session_id:
        h["Mcp-Session-Id"] = session_id
    return h


def rpc(method, params=None, session_id=None, notify=False):
    global _id
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        _id += 1
        body["id"] = _id
    r = requests.post(URL, headers=_headers(session_id), json=body, timeout=180)
    if r.status_code >= 400:
        raise SystemExit(f"HTTP {r.status_code} on {method}: {r.text[:2000]}")
    sid = r.headers.get("Mcp-Session-Id", session_id)
    if notify or not r.text.strip():
        return None, sid
    if r.headers.get("Content-Type", "").startswith("text/event-stream"):
        data = [l[5:].strip() for l in r.text.splitlines() if l.startswith("data:")]
        msg = json.loads(data[-1])
    else:
        msg = r.json()
    return msg, sid


def session():
    msg, sid = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "probe", "version": "0.1"}})
    rpc("notifications/initialized", session_id=sid, notify=True)
    return msg, sid


if __name__ == "__main__":
    init, sid = session()
    if sys.argv[1] == "list":
        print("server:", json.dumps(init.get("result", {}).get("serverInfo")))
        tools, _ = rpc("tools/list", session_id=sid)
        print(json.dumps(tools, indent=2))
    elif sys.argv[1] == "call":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        res, _ = rpc("tools/call", {"name": sys.argv[2], "arguments": args}, session_id=sid)
        print(json.dumps(res, indent=2))
