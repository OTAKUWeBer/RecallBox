import sys
import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

# Configure stderr logging so stdout is dedicated purely to JSON-RPC MCP messages
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [MCP] %(message)s"
)
logger = logging.getLogger("recallbox.mcp")

API_BASE_URL = os.getenv("RECALLBOX_API_URL", "http://127.0.0.1:8765/api/v1")
ALLOW_DESTRUCTIVE = os.getenv("RECALLBOX_MCP_ALLOW_DESTRUCTIVE", "false").lower() in ("true", "1", "yes")

def get_auth_token() -> Optional[str]:
    env_token = os.getenv("RECALLBOX_API_KEY")
    if env_token:
        return env_token.strip()
    for candidate in [
        Path.cwd() / "data" / "auth_token",
        Path.cwd().parent / "data" / "auth_token",
        Path.cwd().parent.parent / "data" / "auth_token",
        Path.home() / ".recallbox" / "auth_token"
    ]:
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    return None

class RecallBoxMCPServer:
    """
    Model Context Protocol (MCP) standard server for RecallBox.
    Enables Claude Desktop, Cursor, and any MCP client to query and write to the user's personal memory.
    """

    def __init__(self):
        token = get_auth_token()
        headers = {}
        if token:
            headers["X-RecallBox-Key"] = token
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=15.0)

    async def list_tools(self) -> List[Dict[str, Any]]:
        tools = [
            {
                "name": "recall",
                "description": "Search personal memory using natural language, keywords, or topics. Returns relevant memories with context.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language query, topic, or keyword"},
                        "limit": {"type": "integer", "description": "Max results to return (default: 5)", "default": 5},
                        "tag": {"type": "string", "description": "Optional tag filter"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "remember",
                "description": "Capture a decision, note, URL, or finding into RecallBox with optional intent ('why').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Note, text, decision, or finding to remember"},
                        "title": {"type": "string", "description": "Optional concise title"},
                        "why": {"type": "string", "description": "Why are you saving this? (User intent or goal)"},
                        "source_url": {"type": "string", "description": "Optional reference URL"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tags (e.g. ['docker', 'decision'])"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "get_context",
                "description": "Extract compact, high-signal context and decisions about a topic or project across personal memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic, project, or tool name"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "list_recent",
                "description": "List recently captured memories and decisions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of items to fetch (default: 10)", "default": 10}
                    }
                }
            },
            {
                "name": "get_memory",
                "description": "Fetch detailed contents and 'Why did I save this?' context for a specific memory ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "The unique ID of the memory"}
                    },
                    "required": ["memory_id"]
                }
            },
            {
                "name": "get_digest",
                "description": "Retrieve weekly synthesis, top topics, and forgotten ideas from memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_reminder",
                "description": "Schedule a reminder for a memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "Memory ID to attach reminder to"},
                        "remind_at": {"type": "string", "description": "ISO 8601 timestamp for reminder"},
                        "note": {"type": "string", "description": "Reminder note"}
                    },
                    "required": ["memory_id", "remind_at"]
                }
            }
        ]

        if ALLOW_DESTRUCTIVE:
            tools.append({
                "name": "forget",
                "description": "Permanently delete a memory. DANGEROUS: Requires explicit user_confirmation parameter set to true.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "Memory ID to delete"},
                        "user_confirmation": {"type": "boolean", "description": "Must be true to proceed with deletion"}
                    },
                    "required": ["memory_id", "user_confirmation"]
                }
            })

        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name in ("recall", "search"):
                resp = await self.client.post("/search", json={
                    "query": arguments.get("query", ""),
                    "limit": arguments.get("limit", 5),
                    "tag": arguments.get("tag")
                })
                data = resp.json()
                results = data.get("results", [])
                formatted = []
                for item in results:
                    m = item["memory"]
                    formatted.append({
                        "id": m["id"],
                        "title": m["title"],
                        "summary": m["summary"],
                        "why": m.get("user_why"),
                        "tags": m.get("tags", []),
                        "url": m.get("source_url"),
                        "relevance_score": item.get("score")
                    })
                return {"content": [{"type": "text", "text": json.dumps(formatted, indent=2)}]}

            elif name == "remember":
                payload = {
                    "title": arguments.get("title"),
                    "content": arguments.get("content"),
                    "user_why": arguments.get("why"),
                    "source_url": arguments.get("source_url"),
                    "tags": arguments.get("tags", []),
                    "source": "mcp"
                }
                resp = await self.client.post("/memories", json=payload)
                if resp.status_code == 201:
                    m = resp.json()
                    return {"content": [{"type": "text", "text": f"Successfully remembered: '{m['title']}' (ID: {m['id']})"}]}
                return {"isError": True, "content": [{"type": "text", "text": f"Failed to save: {resp.text}"}]}

            elif name == "get_context":
                topic = arguments.get("topic", "")
                resp = await self.client.post("/search", json={"query": topic, "limit": 6})
                data = resp.json()
                results = data.get("results", [])
                summary_lines = [f"# Memory Context for: {topic}\n"]
                for item in results:
                    m = item["memory"]
                    summary_lines.append(f"## {m['title']}")
                    if m.get("user_why"):
                        summary_lines.append(f"> **Why saved:** {m['user_why']}")
                    summary_lines.append(f"{m.get('summary') or m.get('content')[:200]}")
                    if m.get("source_url"):
                        summary_lines.append(f"Link: {m['source_url']}")
                    summary_lines.append("")
                return {"content": [{"type": "text", "text": "\n".join(summary_lines)}]}

            elif name == "list_recent":
                limit = arguments.get("limit", 10)
                resp = await self.client.get(f"/memories?limit={limit}")
                return {"content": [{"type": "text", "text": json.dumps(resp.json(), indent=2)}]}

            elif name == "get_memory":
                mem_id = arguments.get("memory_id")
                resp = await self.client.get(f"/memories/{mem_id}")
                ctx_resp = await self.client.get(f"/context/{mem_id}")
                mem_data = resp.json()
                if ctx_resp.status_code == 200:
                    mem_data["reconstructed_context"] = ctx_resp.json()
                return {"content": [{"type": "text", "text": json.dumps(mem_data, indent=2)}]}

            elif name == "get_digest":
                resp = await self.client.get("/digest")
                return {"content": [{"type": "text", "text": json.dumps(resp.json(), indent=2)}]}

            elif name == "create_reminder":
                mem_id = arguments.get("memory_id")
                payload = {
                    "memory_id": mem_id,
                    "remind_at": arguments.get("remind_at"),
                    "note": arguments.get("note")
                }
                resp = await self.client.post(f"/memories/{mem_id}/remind", json=payload)
                return {"content": [{"type": "text", "text": json.dumps(resp.json(), indent=2)}]}

            elif name == "forget":
                if not ALLOW_DESTRUCTIVE:
                    return {
                        "isError": True,
                        "content": [{
                            "type": "text",
                            "text": "Destructive operation blocked: The 'forget' tool is disabled by default in RecallBox MCP to protect against indirect prompt injection. Set RECALLBOX_MCP_ALLOW_DESTRUCTIVE=true in your environment to enable."
                        }]
                    }
                if not arguments.get("user_confirmation"):
                    return {
                        "isError": True,
                        "content": [{
                            "type": "text",
                            "text": "Dangerous action aborted: user_confirmation must be explicitly true."
                        }]
                    }
                mem_id = arguments.get("memory_id")
                resp = await self.client.delete(f"/memories/{mem_id}")
                if resp.status_code == 204:
                    return {"content": [{"type": "text", "text": f"Memory {mem_id} permanently forgotten."}]}
                return {"isError": True, "content": [{"type": "text", "text": f"Delete failed: {resp.text}"}]}

            else:
                return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"isError": True, "content": [{"type": "text", "text": f"Tool execution failed: {str(e)}"}]}

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = request.get("method")
        msg_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "recallbox-mcp", "version": "0.1.0"}
                }
            }
        elif method == "tools/list":
            tools = await self.list_tools()
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            result = await self.call_tool(name, args)
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        elif method == "notifications/initialized":
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }

    async def run_stdio(self):
        logger.info("RecallBox MCP Server running on stdio...")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            line = await reader.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                req = json.loads(line_str)
                resp = await self.handle_request(req)
                if resp:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                logger.error(f"Failed to handle JSON-RPC line: {e}")

if __name__ == "__main__":
    server = RecallBoxMCPServer()
    asyncio.run(server.run_stdio())
