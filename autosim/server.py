"""Small same-origin HTTP API and static frontend for local development."""

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from .adapters import PreviewAdapter
from .domain import ValidationError, parse_mission
from .store import RunStore

WEB = Path(__file__).parent / "web"
STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8")}
MAX_BODY = 32_768


def make_server(host="127.0.0.1", port=8000, db_path="data/autosim.sqlite3", adapter=None):
    store = RunStore(db_path)
    simulator = adapter if adapter is not None else PreviewAdapter()

    class Handler(BaseHTTPRequestHandler):
        # Bound idle reads; this remains a local development server.
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def send_body(self, status, body, content_type="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def reply(self, status, payload):
            self.send_body(status, json.dumps(payload, allow_nan=False).encode())

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in STATIC:
                filename, content_type = STATIC[path]
                self.send_body(200, (WEB / filename).read_bytes(), content_type)
            elif path == "/api/health":
                self.reply(200, {"status": "ok", "adapter": simulator.name})
            elif path == "/api/runs":
                self.reply(200, {"runs": store.recent()})
            elif path.startswith("/api/runs/"):
                run = store.get(path.removeprefix("/api/runs/"))
                self.reply(200, run) if run else self.reply(404, {"error": "Run not found."})
            else:
                self.reply(404, {"error": "Route not found."})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/missions":
                self.reply(404, {"error": "Route not found."})
                return
            if self.headers.get_content_type() != "application/json":
                self.reply(415, {"error": "Use Content-Type: application/json."})
                return
            if self.headers.get("Transfer-Encoding"):
                self.reply(400, {"error": "Transfer-Encoding is not supported."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = -1
            if not 0 < size <= MAX_BODY:
                self.reply(413, {"error": "Request body must contain 1–32768 bytes."})
                return
            try:
                payload = json.loads(self.rfile.read(size))
                mission = parse_mission(payload)
            except (ValueError, UnicodeError, RecursionError) as exc:
                message = str(exc) if isinstance(exc, ValidationError) else "Invalid JSON request."
                self.reply(400, {"error": message})
                return
            try:
                result = simulator.run(mission)
                run = {**result, "id": str(uuid4()),
                       "created_at": datetime.now(timezone.utc).isoformat(),
                       "mission": mission.to_dict()}
                store.save(run)
            except Exception:
                logging.exception("Mission execution or persistence failed")
                self.reply(500, {"error": "Could not generate and save this run."})
                return
            self.reply(201, run)

    return ThreadingHTTPServer((host, port), Handler)
