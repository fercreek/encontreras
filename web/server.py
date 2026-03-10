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
        elif self.path == "/api/files":
            self._serve_file_list()
        else:
            super().do_GET()

    def _serve_json_data(self):
        """Return the most recent JSON output file."""
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


def start_server(output_dir: str = "./output", port: int = DEFAULT_PORT):
    """Start the dashboard server."""
    DashboardHandler.output_dir = output_dir

    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    console.print(f"\n[bold cyan]🖥  Dashboard encontreras[/bold cyan]")
    console.print(f"[green]   → http://localhost:{port}[/green]")
    console.print(f"[dim]   Datos desde: {output_dir}[/dim]")
    console.print(f"[dim]   Ctrl+C para detener[/dim]\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard detenido.[/yellow]")
        server.server_close()
