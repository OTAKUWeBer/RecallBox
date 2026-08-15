# RecallBox Model Context Protocol (MCP) Guide

RecallBox includes first-class support for the **Model Context Protocol (MCP)** via the `packages/mcp` package. This enables AI assistants such as **Claude Desktop**, **Cursor**, and any MCP client to query and write directly to your local RecallBox personal memory vault.

---

## 🛠️ Available MCP Tools

### Read Tools (Safe)
| Tool | Description |
| :--- | :--- |
| `recall(query, limit=5, tag=None)` | Natural language hybrid lexical + semantic search over personal memories. |
| `get_context(topic)` | Generates compact, high-signal topic or project context with why-saved intent. |
| `list_recent(limit=10)` | Lists the most recently captured discoveries and decisions. |
| `get_memory(memory_id)` | Fetches complete memory details and reconstructed temporal context. |
| `get_digest()` | Retrieves weekly synthesis, top topics, and forgotten ideas. |

### Write Tools
| Tool | Description |
| :--- | :--- |
| `remember(content, title=None, why=None, source_url=None, tags=[])` | Stores a note, decision, link, or finding in RecallBox. |
| `create_reminder(memory_id, remind_at, note)` | Schedules a follow-up action reminder. |

### Destructive Tools (Gated)
| Tool | Description | Safety Policy |
| :--- | :--- | :--- |
| `forget(memory_id, user_confirmation)` | Permanently deletes a memory. | **Disabled by default**. Requires `RECALLBOX_MCP_ALLOW_DESTRUCTIVE=true`. |

---

## 🔒 Security Model & Indirect Prompt Injection Defense

1. **Destructive Tool Gating**: To protect against indirect prompt injection (e.g. an AI reading an untrusted webpage or document that contains instructions to delete memories), the `forget` tool is **disabled by default**.
2. **Enabling Destructive Actions**: If you explicitly want your MCP assistant to be able to delete memories, you must set:
   ```env
   RECALLBOX_MCP_ALLOW_DESTRUCTIVE=true
   ```
3. **Local Loopback Auth**: The MCP server automatically resolves the local authorization token from `data/auth_token` or `RECALLBOX_API_KEY`.

---

## 🤖 Configuring Claude Desktop

Add RecallBox MCP to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "recallbox": {
      "command": "python",
      "args": [
        "/absolute/path/to/recallbox/packages/mcp/recallbox_mcp.py"
      ],
      "env": {
        "RECALLBOX_API_URL": "http://127.0.0.1:8765/api/v1",
        "RECALLBOX_MCP_ALLOW_DESTRUCTIVE": "false"
      }
    }
  }
}
```

---

## 💬 Example AI Prompts

**Querying Past Memories:**
> **User:** *"What was that Docker monitoring tool I saved a couple of weeks ago?"*  
> **Assistant:** *(Invokes `recall(query="Docker monitoring")`)*  
> **Assistant:** *"You saved **Prometheus Docker Container Monitoring** 14 days ago. You noted: 'Benchmark for VPS cluster metrics'."*

**Capturing Decisions on the Fly:**
> **User:** *"Remember that we decided to use SQLite with WAL mode for our storage engine."*  
> **Assistant:** *(Invokes `remember(content="Decided to use SQLite with WAL mode for storage engine.", why="Architecture decision for local search", tags=["sqlite", "architecture", "decision"])`)*  
> **Assistant:** *"Saved to your RecallBox memory vault."*
