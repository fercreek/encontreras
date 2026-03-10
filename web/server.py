"""
Lightweight dashboard server for encontreras.

Uses Python's built-in http.server — no Flask needed.
Serves the web/ static files and provides a /api/data endpoint
that reads the most recent JSON output.
"""

from __future__ import annotations

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from rich.console import Console

console = Console()

DEFAULT_PORT = 8888


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serve static files from web/ and the JSON data via /api/data."""

    output_dir: str = "./output"

    def __init__(self, *args, **kwargs):
        # Serve files from the web/ directory
        web_dir = str(Path(__file__).parent)
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_GET(self):
        if self.path == "/api/data":
            self._serve_json_data()
        elif self.path == "/api/status":
            self._serve_status()
        elif self.path == "/api/files":
            self._serve_file_list()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                import json
                import subprocess
                import sys
                
                payload = json.loads(post_data.decode("utf-8"))
                query = payload.get("query")
                location = payload.get("location")
                max_results = payload.get("max_results", 10)
                
                if not query or not location:
                    self._json_response({"error": "Missing query or location"}, 400)
                    return
                
                # Enqueue the background job using Huey
                root_dir = Path(__file__).parent.parent
                from src.core.tasks import run_extraction_job
                
                run_extraction_job(
                    query=query, 
                    location=location, 
                    max_results=max_results, 
                    output_dir=str(root_dir / "output")
                )
                
                self._json_response({"status": "Started extraction in background (Huey Queue)"})
                
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_status(self):
        """Return the current extraction status if a background job is running."""
        try:
            status_file = Path(self.output_dir) / "running_status.json"
            if status_file.exists():
                data = json.loads(status_file.read_text(encoding="utf-8"))
                self._json_response({"running": True, **data})
            else:
                self._json_response({"running": False})
        except Exception as e:
            self._json_response({"running": False, "error": str(e)})

    def _serve_json_data(self):
        """Return the most recent data from SQLite or JSON fallback."""
        import sqlite3
        db_path = Path(self.output_dir) / "encontreras.db"
        
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM businesses ORDER BY updated_at DESC")
                rows = cursor.fetchall()
                
                businesses = []
                for r in rows:
                    b = dict(r)
                    if b.get("emails"):
                        b["emails"] = b["emails"].split(",")
                    else:
                        b["emails"] = []
                        
                    if b.get("site_issues"):
                        b["site_issues"] = b["site_issues"].split(",")
                    else:
                        b["site_issues"] = []
                        
                    businesses.append(b)
                    
                conn.close()
                self._json_response({
                    "file": "encontreras.db (SQLite)",
                    "count": len(businesses),
                    "businesses": businesses,
                })
                return
            except Exception as e:
                self._json_response({"error": f"SQLite Database Error: {str(e)}", "businesses": []}, 500)
                return

        # Fallback to json files (legacy)
        output_path = Path(self.output_dir)
        json_files = sorted(output_path.glob("encontreras_*.json"), reverse=True)

        if not json_files:
            self._json_response({"error": "No data found", "businesses": []}, 404)
            return

        latest = json_files[0]
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            self._json_response({
                "file": latest.name,
                "count": len(data),
                "businesses": data,
            })
        except Exception as e:
            self._json_response({"error": str(e), "businesses": []}, 500)

    def _serve_file_list(self):
        """Return list of available output files."""
        output_path = Path(self.output_dir)
        files = []
        for f in sorted(output_path.glob("encontreras_*"), reverse=True):
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": f.suffix.lstrip("."),
            })
        self._json_response({"files": files})

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default logging noise."""
        pass


class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

def start_server(output_dir: str = "./output", port: int = DEFAULT_PORT):
    """Start the dashboard server."""
    DashboardHandler.output_dir = output_dir

    server = ReuseHTTPServer(("0.0.0.0", port), DashboardHandler)
    console.print(f"\n[bold cyan]🖥  Dashboard encontreras[/bold cyan]")
    console.print(f"[green]   → http://localhost:{port}[/green]")
    console.print(f"[dim]   Datos desde: {output_dir}[/dim]")
    console.print(f"[dim]   Ctrl+C para detener[/dim]\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard detenido.[/yellow]")
        server.server_close()
