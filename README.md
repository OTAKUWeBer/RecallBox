<div align="center">

# 🧠 RecallBox

> **Never lose something you wanted to come back to.**

**RecallBox is an open-source, local-first personal memory system for everything you discover, decide, and research online.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org)
[![Protocol: MCP](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol%20(MCP)-8B5CF6.svg)](https://modelcontextprotocol.io)
[![Privacy: Local-First](https://img.shields.io/badge/Privacy-Local--First%20%26%20Private-10B981.svg)](#-privacy--data-ownership)

</div>

---

### 💡 Why RecallBox?

**Bookmarks remember *what* you saved. RecallBox helps you remember *why* you saved it.**

Every day, you discover valuable insights across the web:
- **Save a GitHub repository** with an interesting architecture or monitoring pipeline.
- **Save a Reddit discussion** solving a subtle database locking issue.
- **Save an article or benchmark** you want to test on your own machine.
- **Save a technical decision** along with your original reasoning.

Weeks later, search or ask: *"Why did I save this?"*  
RecallBox reconstructs your factual research session ($\pm 24\text{h}$ temporal cluster), preserves your original intent, and links related memories in an interactive Knowledge Graph—all stored locally on your device with **$0 hosting cost**.

---

## 🎯 Who is it for?

- **Software Engineers & Architects**: Capture repositories, documentation, benchmarks, and decisions without losing context.
- **Researchers & Students**: Organize research papers, cross-reference articles, and trace multi-day discovery trails.
- **Privacy-Conscious Users**: Keep your personal second brain on your own hardware without subscriptions, mandatory cloud accounts, or lock-in.
- **AI Power Users**: Connect RecallBox directly to Claude Desktop, Cursor, or local LLMs using the Model Context Protocol (MCP).

---

## ✨ Key Features (Built & Verified)

- 🔒 **Local-First SQLite Storage**: Embedded SQLite with WAL mode and FTS5 full-text indexing. No mandatory server or cloud account required.
- ⚡ **Sub-Second Capture**: Save pages, selected text, or notes via the Chromium browser extension, terminal CLI, or Web UI.
- ❓ **Context Reconstruction ("Why did I save this?")**: Reconstructs your factual research session ($\pm 24\text{h}$ temporal cluster) and intent trail with zero AI hallucination.
- 🔍 **Hybrid Lexical & Semantic Search**: Combines SQLite FTS5 (BM25) text ranking, local dense vector cosine similarity, Reciprocal Rank Fusion (RRF), recency decay, and importance weighting.
- 🕸️ **Interactive Knowledge Graph**: Explore associative relationship edges (`related_to`, `supports`, `contradicts`, `part_of`, `follow_up_to`) across your memories.
- ⏰ **Actionable Follow-Ups**: Schedule reminders (`Try locally`, `Read docs`, `Benchmark`) so saved ideas don't get lost in a digital hoard.
- 🤖 **AI is Optional**: Runs locally out-of-the-box using built-in heuristic sentence extraction and local feature hashing. Pluggable adapters are available for local **Ollama** or **OpenAI-compatible** endpoints.
- 🔌 **Model Context Protocol (MCP)**: Native stdio JSON-RPC server (`packages/mcp`) allowing AI assistants to query your memory vault securely.
- 📦 **Complete Export & Import**: Export your entire vault anytime as a downloadable ZIP containing individual Markdown files with YAML frontmatter, JSON dumps, and graph data. Import existing bookmarks from Chrome, Brave, Safari, Edge, or Firefox.

---

## 🔒 Privacy & Data Ownership

RecallBox is **local-first**. No hosted account or mandatory third-party service is required.

| Aspect | Behavior in RecallBox |
| :--- | :--- |
| **Where data is stored** | Stored locally on your machine in `data/recallbox.db` and `data/auth_token`. |
| **Telemetry & Analytics** | **0% Telemetry**. No analytics SDKs, no tracking pixels, no telemetry beacons. |
| **Local Operation** | Most functionality runs locally: creating notes, searching, context reconstruction, reminders, and export do not require external services. |
| **URL Captures** | Saving a remote URL requires an outbound request to that public webpage so RecallBox can extract metadata. Hop-by-hop SSRF protection blocks private network scanning. |
| **Cloud AI (Optional)** | If and only if you explicitly configure an external AI provider (e.g. `OPENAI_API_KEY`), prompt text and search queries are sent over TLS to that specific endpoint. |
| **Data Backup** | Simply copy `data/recallbox.db` or click **Export ZIP** in the Privacy Center to get standard Markdown files. |
| **Complete Deletion** | You can permanently purge all database records and indices via the Privacy Center or by deleting the `data/` directory. |

---

## 🏛️ System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                   Chromium Extension                     │ (Manifest V3)
└────────────────────────────┬─────────────────────────────┘
                             │ HTTP + X-RecallBox-Key
┌─────────────────────────┐  ▼   ┌─────────────────────────┐
│     RecallBox CLI       ├─────►│     FastAPI Backend     │◄─── React Web UI
│       (Typer)           │      │ (127.0.0.1:8765 REST v1)│     (Vite + Tailwind)
└─────────────────────────┘      └───────────┬─────────────┘
┌─────────────────────────┐                  │
│    recallbox-mcp        ├──────────────────┤
│ (Claude / Cursor MCP)   │                  ▼
└─────────────────────────┘      ┌─────────────────────────┐
                                 │    Context Engine &     │
                                 │    Duplicate Detector   │
                                 └───────────┬─────────────┘
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ▼                                                     ▼
       ┌────────────────────────┐                            ┌────────────────────────┐
       │ SQLite FTS5 BM25 Index │                            │   Local Vector Store   │
       │ (Lexical & Full-text)  │                            │ (Cosine Similarity)    │
       └──────────┬─────────────┘                            └──────────┬─────────────┘
                  │                                                     │
                  └──────────────────────────┬──────────────────────────┘
                                             ▼
                                 ┌────────────────────────┐
                                 │ Reciprocal Rank Fusion │
                                 │ (Hybrid Fusion Search) │
                                 └────────────────────────┘
```

---

## 🚀 Quick Start

### Option A: Run with Docker Compose (Fastest)

```bash
git clone https://github.com/OTAKUWeBer/RecallBox.git && cd RecallBox
docker compose up -d
```
- **Web UI**: Open [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://127.0.0.1:8765/api/v1](http://127.0.0.1:8765/api/v1)
- **Health Check**: [http://127.0.0.1:8765/api/v1/health](http://127.0.0.1:8765/api/v1/health)

---

### Option B: Local Development Setup

#### Prerequisites
- **Python 3.11+**
- **[Bun](https://bun.sh)** (version 1.1+ recommended) or Node.js 20+

#### 1. Backend Setup
```bash
# 1. Create and activate Python virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 2. Install dependencies & CLI
pip install -r backend/requirements.txt
pip install -e packages/cli

# 3. Start FastAPI backend (runs on 127.0.0.1:8765)
cd backend
python -m uvicorn app.main:app --reload --port 8765
```

#### 2. Web Frontend Setup
```bash
# In a new terminal window from repository root:
bun install
bun dev:web
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧩 Browser Extension Setup (Chrome, Brave, Edge, Arc)

1. Open `chrome://extensions/` in any Chromium-based browser.
2. Toggle on **Developer mode** in the top-right corner.
3. Click **Load unpacked** and select the `apps/extension` folder inside this repository.
4. Capture any page with 1 click, right-click any selected text to save a quote, or press `Ctrl+Shift+R` (`Cmd+Shift+R` on macOS).

---

## 🤖 Model Context Protocol (MCP) Setup

Connect RecallBox to **Claude Desktop**, **Cursor**, or any MCP-compliant AI assistant.

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "recallbox": {
      "command": "python",
      "args": [
        "/absolute/path/to/RecallBox/packages/mcp/recallbox_mcp.py"
      ]
    }
  }
}
```

### Available MCP Tools:
- `recall(query, limit=5, tag=None)`: Natural language hybrid search across your personal memories.
- `remember(content, title=None, why=None, source_url=None, tags=[])`: Capture a decision or finding.
- `get_context(topic)`: Retrieve factual summaries and decisions about a topic or project.
- `get_memory(memory_id)`: Fetch detailed content and reconstructed context.
- `list_recent(limit=10)`: List recently saved discoveries.
- `get_digest()`: Retrieve weekly synthesis and forgotten ideas.
- `create_reminder(memory_id, remind_at, note)`: Schedule a follow-up action.
- `forget(memory_id)`: **Permanently delete a memory.** *(Disabled by default for security; see below).*

> [!IMPORTANT]
> **MCP Security Model**: To protect against indirect prompt injection (e.g. an AI reading an untrusted webpage and executing destructive commands), destructive tools like `forget` are **disabled by default**. To enable them, set `RECALLBOX_MCP_ALLOW_DESTRUCTIVE=true` in your MCP environment.

---

## 💻 CLI Usage (`recallbox`)

```bash
# 1. Capture a note, decision, or URL
recallbox remember "https://github.com/prometheus/prometheus" --why "Benchmark for metrics pipeline" --tags "monitoring,docker"

# 2. Hybrid search your vault
recallbox search "PostgreSQL indexing"

# 3. List recent discoveries
recallbox recent --limit 10

# 4. Reconstruct context ("Why did I save this?")
recallbox context <memory-id>

# 5. Run health check & diagnostics
recallbox doctor
```

---

## ⚙️ Environment Configuration

RecallBox works out of the box with zero configuration. Copy `.env.example` to `.env` if you wish to customize options:

| Variable | Required? | Default | Purpose & Security Impact |
| :--- | :---: | :---: | :--- |
| `RECALLBOX_HOST` | No | `127.0.0.1` | Network interface binding. Keep `127.0.0.1` to prevent LAN exposure. |
| `RECALLBOX_PORT` | No | `8765` | Local backend HTTP port. |
| `RECALLBOX_API_KEY` | No | Auto-generated | Local authorization token override. Generated automatically in `data/auth_token` if unset. |
| `RECALLBOX_AI_PROVIDER` | No | `local` | AI backend: `local` (offline heuristic), `ollama`, or `openai`. |
| `RECALLBOX_OLLAMA_URL` | No | `http://127.0.0.1:11434` | Endpoint for local Ollama server. |
| `RECALLBOX_OLLAMA_MODEL` | No | `llama3.2` | Ollama model for summarization and tagging. |
| `RECALLBOX_OLLAMA_EMBED_MODEL` | No | `nomic-embed-text` | Ollama model for dense embeddings. |
| `OPENAI_API_KEY` | No | `""` | Optional API key if using cloud AI (`RECALLBOX_AI_PROVIDER=openai`). |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom endpoint for OpenAI, Groq, DeepSeek, or vLLM. |
| `RECALLBOX_MCP_ALLOW_DESTRUCTIVE` | No | `false` | Set to `true` to allow MCP clients to invoke the `forget` deletion tool. |

---

## 📂 Repository Layout

```
recallbox/
├── apps/
│   ├── web/               # React 18 + Vite + TypeScript + Tailwind CSS web app
│   └── extension/         # Chromium Manifest V3 browser extension
├── packages/
│   ├── mcp/               # Model Context Protocol (@recallbox/mcp) server
│   └── cli/               # RecallBox Python CLI (Typer + Rich)
├── backend/
│   ├── app/
│   │   ├── ai/            # Offline local heuristic, Ollama, and OpenAI adapters
│   │   ├── api/v1/        # REST API endpoints (memories, search, context, privacy, etc.)
│   │   ├── core/          # Database engine, WAL pragmas, and app configuration
│   │   ├── models/        # SQLAlchemy entities and Pydantic v2 schemas
│   │   ├── search/        # SQLite FTS5 lexical, vector index, and RRF hybrid search
│   │   ├── security/      # Local loopback auth, SSRF validator, and HTML sanitizers
│   │   └── services/      # Ingestion, context reconstruction, duplicate detection, export
│   └── tests/             # Pytest automated test suite (20 unit & security tests)
├── docker/                # Multi-stage Dockerfiles (non-root backend & nginx web)
├── docs/                  # Architecture, MCP Guide, Extension Guide, and Self-Hosting
├── docker-compose.yml     # Production single-command deployment
├── LICENSE                # MIT License
├── SECURITY.md            # Vulnerability reporting guidelines
├── CONTRIBUTING.md        # Local development and pull request guide
├── CODE_OF_CONDUCT.md     # Contributor Covenant v2.1
└── README.md
```

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><strong>Does RecallBox require an API key or paid subscription?</strong></summary>
<p>No. RecallBox is 100% free and open source. The default configuration uses embedded SQLite, local FTS5 search, and built-in offline sentence extraction requiring zero external tokens or paid APIs.</p>
</details>

<details>
<summary><strong>Does my data ever leave my computer?</strong></summary>
<p>Your stored data remains local by default. Saving a remote URL requires RecallBox to fetch that URL, and optional cloud AI providers can receive data when explicitly configured.</p>
</details>

<details>
<summary><strong>How do I back up my memories?</strong></summary>
<p>You can click <strong>Export ZIP</strong> in the Privacy Center or make a copy of the <code>data/recallbox.db</code> file. The ZIP export produces standard Markdown files with YAML frontmatter that can be read by Obsidian, Notion, or any text editor.</p>
</details>

<details>
<summary><strong>How do I completely delete all my data?</strong></summary>
<p>Go to the <strong>Privacy Center</strong> in the Web UI, click <strong>Purge All Data</strong>, and type <code>PERMANENTLY PURGE ALL DATA</code> to confirm. Alternatively, stop the backend and delete the <code>data/</code> folder.</p>
</details>

<details>
<summary><strong>What happens if I lose my local auth token?</strong></summary>
<p>The auth token is stored in <code>data/auth_token</code>. If deleted while the backend is stopped, a fresh secure token is automatically generated on next startup. The local Web UI auto-syncs with the backend over loopback.</p>
</details>

---

## 🛠️ Troubleshooting

- **Port 8765 already in use**: Change `RECALLBOX_PORT=8766` in your `.env` file or terminate the conflicting process.
- **Browser Extension shows error badge**: Ensure the backend server is running on `http://127.0.0.1:8765`. Test by opening `http://127.0.0.1:8765/api/v1/health` in your browser.
- **Database is locked**: RecallBox uses SQLite in WAL mode. Ensure you are not running two backend instances pointing to the same database directory concurrently.

---

## 🧪 Testing & Validation

```bash
# Run backend pytest suite (20 unit, search, SSRF, XSS, and auth tests)
pytest -v backend/tests/

# Build frontend production bundle with TypeScript checks
bun --cwd apps/web build
```

---

## 📄 Documentation Links

- [Architecture & Search Fusion](docs/ARCHITECTURE.md)
- [Model Context Protocol (MCP) Guide](docs/MCP_GUIDE.md)
- [Browser Extension Setup](docs/EXTENSION_GUIDE.md)
- [Self-Hosting & Docker Guide](docs/SELF_HOSTING.md)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 📄 License

RecallBox is open-source software licensed under the [MIT License](LICENSE).
