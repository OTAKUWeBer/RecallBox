import sys
import os
import json
import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
import httpx

app = typer.Typer(
    name="recallbox",
    help="RecallBox CLI: Local-first personal memory system. Never lose something you wanted to come back to.",
    add_completion=False
)
console = Console()

from pathlib import Path

API_BASE_URL = os.getenv("RECALLBOX_API_URL", "http://127.0.0.1:8765/api/v1")

def get_auth_token() -> Optional[str]:
    env_token = os.getenv("RECALLBOX_API_KEY")
    if env_token:
        return env_token.strip()
    # Check default local data/auth_token path
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

def get_client() -> httpx.Client:
    token = get_auth_token()
    headers = {}
    if token:
        headers["X-RecallBox-Key"] = token
    return httpx.Client(base_url=API_BASE_URL, headers=headers, timeout=15.0)

@app.command()
def remember(
    content_or_url: str = typer.Argument(..., help="Text note, URL, or idea to capture"),
    why: Optional[str] = typer.Option(None, "--why", "-w", help="Why are you saving this? (Intent note)"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags (e.g. 'docker,devops')"),
    remind: Optional[str] = typer.Option(None, "--remind", "-r", help="Optional reminder date (e.g. '2026-08-20')")
):
    """Capture a new memory into RecallBox."""
    with console.status("[bold cyan]Saving memory to RecallBox...[/bold cyan]"):
        is_url = content_or_url.startswith("http://") or content_or_url.startswith("https://")
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        
        payload = {
            "source": "cli",
            "source_url": content_or_url if is_url else None,
            "content": "" if is_url else content_or_url,
            "title": None if is_url else content_or_url[:60],
            "user_why": why,
            "tags": tag_list
        }
        
        try:
            with get_client() as client:
                resp = client.post("/memories", json=payload)
                if resp.status_code == 201:
                    data = resp.json()
                    console.print(Panel(
                        f"[bold green]✓ Saved to RecallBox![/bold green]\n\n"
                        f"[bold]Title:[/bold] {data['title']}\n"
                        f"[bold]ID:[/bold] [dim]{data['id']}[/dim]\n"
                        f"[bold]Summary:[/bold] {data['summary'] or 'No summary'}\n"
                        f"[bold]Tags:[/bold] {', '.join(data['tags']) if data['tags'] else 'none'}\n"
                        f"[bold]Why:[/bold] {data['user_why'] or '[dim]none[/dim]'}",
                        title="Memory Captured",
                        border_style="green"
                    ))
                else:
                    console.print(f"[bold red]Error saving memory ({resp.status_code}):[/bold red] {resp.text}")
        except Exception as e:
            console.print(f"[bold red]Could not connect to RecallBox backend:[/bold red] {e}")
            console.print("[yellow]Tip: Make sure RecallBox server is running with 'recallbox serve' or 'python -m uvicorn app.main:app'[/yellow]")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (natural language, keywords, or topics)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results to return"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag")
):
    """Search your personal memories using hybrid lexical + semantic search."""
    with console.status(f"[bold cyan]Searching memories for '{query}'...[/bold cyan]"):
        try:
            with get_client() as client:
                resp = client.post("/search", json={"query": query, "limit": limit, "tag": tag})
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if not results:
                        console.print(f"[yellow]No memories found matching '{query}'.[/yellow]")
                        return
                        
                    table = Table(title=f"Search Results for '{query}' ({data.get('total_results')} matches)", show_lines=True)
                    table.add_column("Score", justify="right", style="cyan", width=8)
                    table.add_column("Title & Summary", style="white")
                    table.add_column("Tags & Source", style="dim", width=25)
                    table.add_column("ID", style="dim", width=12)
                    
                    for item in results:
                        mem = item["memory"]
                        score_str = f"{round(item['score'] * 100)}%"
                        title_summary = f"[bold]{mem['title']}[/bold]\n{mem['summary'][:120]}..."
                        if mem.get("user_why"):
                            title_summary += f"\n[italic cyan]Why: {mem['user_why']}[/italic cyan]"
                        tags_str = f"Tags: {', '.join(mem['tags'][:3])}\nSource: {mem['source_type']}"
                        table.add_row(score_str, title_summary, tags_str, mem["id"][:8] + "...")
                        
                    console.print(table)
                else:
                    console.print(f"[bold red]Search failed ({resp.status_code}):[/bold red] {resp.text}")
        except Exception as e:
            console.print(f"[bold red]Search connection error:[/bold red] {e}")

@app.command()
def recent(limit: int = typer.Option(10, "--limit", "-l", help="Number of recent items")):
    """List recently captured memories."""
    try:
        with get_client() as client:
            resp = client.get(f"/memories?limit={limit}")
            if resp.status_code == 200:
                memories = resp.json()
                if not memories:
                    console.print("[yellow]Your RecallBox is currently empty. Try saving something with 'recallbox remember <url>'![/yellow]")
                    return
                    
                table = Table(title="Recent Memories", show_lines=True)
                table.add_column("Title", style="bold white")
                table.add_column("Type", style="cyan", width=12)
                table.add_column("Captured", style="dim", width=18)
                table.add_column("Tags", style="magenta", width=20)
                table.add_column("ID", style="dim", width=12)
                
                for m in memories:
                    cap_date = m["captured_at"][:10] if m.get("captured_at") else "unknown"
                    table.add_row(
                        m["title"][:50],
                        m.get("source_type", "article"),
                        cap_date,
                        ", ".join(m.get("tags", [])[:3]),
                        m["id"][:8] + "..."
                    )
                console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error fetching recent memories:[/bold red] {e}")

@app.command()
def context(memory_id: str = typer.Argument(..., help="Memory ID to inspect context for")):
    """Reconstruct 'Why did I save this?' context for a specific memory."""
    with console.status("[bold cyan]Reconstructing memory context...[/bold cyan]"):
        try:
            with get_client() as client:
                resp = client.get(f"/context/{memory_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    panel_text = (
                        f"[bold yellow]Memory:[/bold yellow] {data['title']}\n"
                        f"[bold yellow]Timeline:[/bold yellow] Saved {data['saved_days_ago']} days ago ({data['captured_at'][:10]})\n\n"
                        f"[bold green]Context Synthesis:[/bold green]\n{data['context_summary']}\n\n"
                    )
                    if data.get("active_research_trail"):
                        panel_text += f"[bold cyan]Active Research Trail:[/bold cyan] {', '.join(data['active_research_trail'])}\n\n"
                        
                    if data.get("related_memories_saved_around_then"):
                        panel_text += "[bold]Related items saved around then:[/bold]\n"
                        for rm in data["related_memories_saved_around_then"]:
                            panel_text += f" • {rm['title']} [dim]({rm['relationship']})[/dim]\n"
                            
                    console.print(Panel(panel_text, title="Why Did I Save This?", border_style="yellow"))
                else:
                    console.print(f"[bold red]Error ({resp.status_code}):[/bold red] {resp.text}")
        except Exception as e:
            console.print(f"[bold red]Context reconstruction failed:[/bold red] {e}")

@app.command()
def doctor():
    """Run health check and diagnostics on RecallBox installation."""
    console.print("[bold]Running RecallBox Diagnostics...[/bold]\n")
    try:
        with get_client() as client:
            resp = client.get("/health")
            if resp.status_code == 200:
                data = resp.json()
                console.print(f" [bold green]✓[/bold green] Backend API: Online ({API_BASE_URL})")
                console.print(f" [bold green]✓[/bold green] Version: {data.get('version')}")
                console.print(f" [bold green]✓[/bold green] AI Provider: {data.get('ai_provider')} (Offline-ready)")
            else:
                console.print(f" [bold red]✗[/bold red] Backend API returned status {resp.status_code}")
                
            priv_resp = client.get("/privacy/stats")
            if priv_resp.status_code == 200:
                pdata = priv_resp.json()
                console.print(f" [bold green]✓[/bold green] Stored Memories: {pdata.get('stored_memories_count')}")
                console.print(f" [bold green]✓[/bold green] Embeddings Indexed: {pdata.get('stored_embeddings_count')}")
                console.print(f" [bold green]✓[/bold green] Telemetry: {pdata.get('telemetry_status')}")
                console.print(f" [bold green]✓[/bold green] Local Storage: {round(pdata.get('db_size_bytes', 0) / 1024, 1)} KB")
                
    except Exception as e:
        console.print(f" [bold red]✗[/bold red] Backend connection failed: {e}")
        console.print("\n[yellow]To start the backend server, run:[/yellow] recallbox serve")

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8765, "--port", "-p", help="Bind port")
):
    """Start the RecallBox FastAPI backend server locally."""
    console.print(f"[bold green]Starting RecallBox Backend on http://{host}:{port}...[/bold green]")
    import uvicorn
    # Add backend directory to sys.path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)

@app.command()
def mcp():
    """Start the Model Context Protocol (MCP) server over stdio for Claude Desktop, Cursor, etc."""
    mcp_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "mcp", "recallbox_mcp.py"))
    os.execv(sys.executable, [sys.executable, mcp_script])

if __name__ == "__main__":
    app()
