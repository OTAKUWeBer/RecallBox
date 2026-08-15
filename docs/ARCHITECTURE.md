# RecallBox System Architecture

> **"Never lose something you wanted to come back to."**

RecallBox is engineered as a **local-first personal memory operating system**. Unlike conventional bookmarking tools or stateless AI chatbots, RecallBox captures the full situational and temporal context of your discoveries and preserves them in a structured SQLite database.

```
                    ┌────────────────────────┐
                    │   Browser Extension    │ (MV3: Chrome, Brave, Arc, Edge)
                    └───────────┬────────────┘
                                │ HTTP / JSON
┌────────────────────────┐      ▼      ┌────────────────────────┐
│     CLI (Typer)        ├────────────►│     FastAPI Backend    │◄─── RecallBox Web UI
└────────────────────────┘             │  (Port 8765, REST v1)  │     (React + Tailwind)
                                       └───────────┬────────────┘
┌────────────────────────┐                         │
│   recallbox-mcp        ├─────────────────────────┤
│ (Claude/Cursor MCP)    │                         ▼
└────────────────────────┘             ┌────────────────────────┐
                                       │   Context Engine &     │
                                       │   Duplicate Detection  │
                                       └───────────┬────────────┘
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
                                       │  (Hybrid Rank & Score) │
                                       └────────────────────────┘
```

---

## 1. Core Subsystems

### A. Temporal & Associative Context Reconstruction ("Why Did I Save This?")
Traditional tools only store *what* was saved. RecallBox reconstructs *why*:
1. **User Intent Capture**: An optional 1-click `Why are you saving this?` input allows users to annotate explicit goals.
2. **Temporal Research Session Clustering**: When querying "Why did I save this?", RecallBox queries items captured within a $\pm 24\text{h}$ temporal radius.
3. **Cross-Topic Correlation**: Aggregates overlapping entities, tags, and domain trails to explain what thread of research was underway.
4. **Anti-Hallucination Guarantee**: Fact-based synthesis strictly cites stored records and timestamps. If insufficient evidence exists, it states so transparently.

### B. Hybrid Search Engine
Search ranking combines multiple scoring signals:
$$\text{Score} = \text{RRF}(r_{\text{FTS5}}, r_{\text{Vector}}) + w_{\text{recency}} \cdot e^{-\Delta t / \lambda} + w_{\text{importance}} \cdot I + w_{\text{intent}} \cdot \mathbb{I}_{\text{why}} + w_{\text{access}} \cdot \log(1 + N_{\text{access}})$$
- **FTS5 (BM25)**: Fast keyword and prefix matching over title, content, summary, user notes, and tags.
- **Dense Vector Embedding**: 128-dimensional offline semantic embeddings for conceptual matches without requiring cloud tokens.
- **Reciprocal Rank Fusion (RRF)**: Merges rank orderings with constant $k=60$.

### C. Zero-Dependency AI Abstraction
- `LocalHeuristicProvider`: Built-in offline analyzer using extractive sentence ranking, taxonomy pattern matching, and sub-word hashing embeddings. Runs in <5ms.
- `OllamaProvider`: Optional local LLM connection for offline models (`llama3.2`, `nomic-embed-text`).
- `OpenAICompatibleProvider`: Optional OpenAI/Groq/DeepSeek API provider.

### D. Model Context Protocol (`recallbox-mcp`)
Exposes personal memory to AI coding assistants (Claude Desktop, Cursor, Copilot) via stdio JSON-RPC 2.0. Separates read tools (`recall`, `get_context`, `list_recent`) from write tools (`remember`, `create_reminder`) and dangerous tools (`forget`).

---

## 2. Monorepo Structure

| Directory | Role |
| :--- | :--- |
| `apps/web` | React 18 + TypeScript + Tailwind CSS web interface |
| `apps/extension` | Manifest V3 Chromium browser extension |
| `packages/mcp` | Standard Model Context Protocol (MCP) server |
| `packages/cli` | Python CLI tool (`recallbox`) |
| `backend/` | FastAPI backend with SQLite, FTS5, and Hybrid Search |
| `docker/` | Dockerfiles and container configurations |
| `docs/` | Comprehensive technical and user documentation |
