# Contributing to RecallBox

Thank you for your interest in contributing to RecallBox! We welcome pull requests, bug reports, feature suggestions, and documentation enhancements.

---

## 🏛️ Development Philosophy

1. **Local-First & Fast**: Operations should be local, offline-capable, and sub-100ms wherever possible.
2. **AI as an Augmentation, Not a Dependency**: Capture, storage, tag filtering, and hybrid lexical search must function 100% reliably without requiring external AI APIs or cloud tokens.
3. **Strict Privacy**: Zero unsolicited telemetry, zero tracking beacons, and strict local loopback isolation.
4. **Security by Default**: Content from the web must be treated as untrusted; always sanitize scraped input and escape render output.

---

## 📁 Monorepo Layout

- `apps/web/`: React 18 + Vite + TypeScript + Tailwind CSS web interface.
- `apps/extension/`: Chromium Manifest V3 browser extension.
- `packages/mcp/`: RecallBox Model Context Protocol (MCP) server for Claude Desktop, Cursor, etc.
- `packages/cli/`: RecallBox Python Typer CLI (`recallbox`).
- `backend/`: FastAPI backend service with SQLite (WAL mode) and FTS5 indexing.
- `docker/`: Multi-stage Dockerfiles and Compose configurations.

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.11+
- [Bun](https://bun.sh) (version 1.1+ recommended) or Node.js 20+

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/OTAKUWeBer/RecallBox.git
cd recallbox

# 2. Setup Python virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3. Install backend dependencies and CLI
pip install -r backend/requirements.txt
pip install -e packages/cli

# 4. Install web frontend dependencies
bun install

# 5. Start backend development server
cd backend
python -m uvicorn app.main:app --reload --port 8765

# 6. In another terminal, start frontend dev server
bun dev:web
```

---

## 🧪 Running Tests & Quality Checks

Before submitting a Pull Request, verify that all backend tests and frontend builds pass cleanly:

```bash
# Run backend pytest suite (unit, search, security, SSRF, XSS tests)
pytest -v backend/tests/

# Run frontend TypeScript type checking and production build
bun --cwd apps/web build
```

---

## 📋 Pull Request Guidelines

1. **Focused PRs**: Keep changes concise and focused on a single bug fix or feature.
2. **Add Tests**: Include automated unit or integration tests in `backend/tests/` for new endpoints, algorithms, or bug fixes.
3. **Preserve Documentation**: Update `README.md` or `docs/` if changing configuration options or API schemas.
4. **No Secrets**: Never commit `.env` files, API keys, or personal tokens.
