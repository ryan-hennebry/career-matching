"""Serve a validated shortlist over loopback without exposing the working tree."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from run_validation import ROOT, read_object, validate_run

STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/css/dashboard.css": ("css/dashboard.css", "text/css; charset=utf-8"),
    "/js/app.js": ("js/app.js", "text/javascript; charset=utf-8"),
}
PLACEMENTS = {
    "main": {"main"},
    "appendix": {"appendix", "optional", "carry_over_expired"},
}


def presentation_payload(run):
    from career_match import _board_record

    board = read_object(run / "board.json")
    manifest_path = run / "_run-manifest.json"
    manifest = read_object(manifest_path)
    result, records = validate_run(manifest_path, today=manifest.get("run_date"))
    if not result["passed"] or board.get("run_date") != manifest.get("run_date"):
        raise ValueError("dashboard needs a valid, dated run")
    if board.get("synthetic") is not manifest.get("synthetic"):
        raise ValueError("dashboard run mode differs from the manifest")

    exact = dict(zip(manifest["presentation_set"], records))
    output = {"run_date": manifest["run_date"], "synthetic": manifest["synthetic"]}
    for section, places in PLACEMENTS.items():
        try:
            names = manifest["main_set"] if section == "main" else [
                name for name in manifest["presentation_set"] if name not in manifest["main_set"]
            ]
            output[section] = [
                _board_record(exact[name], item["placement"])
                for item, name in zip(board[section], names, strict=True)
                if item["placement"] in places
            ]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("dashboard placement differs from the manifest") from error
        if board[section] != output[section]:
            raise ValueError("dashboard data differs from the validated records")

    coverage = manifest["coverage"]
    output["coverage"] = {
        **{key: coverage[key] for key in ("candidates", "pending", "skipped", "stale")},
        "sources": len(coverage["sources"]),
        "caps_hit": len(coverage["caps_hit"]),
        "blocked_sources": len(coverage["blocked_sources"]),
    }
    return output


def open_server(run, port):
    payload = json.dumps(presentation_payload(run), ensure_ascii=False).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, content_type, body):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", (
                "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            ))
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(body)

        def do_GET(self):
            host = f"127.0.0.1:{self.server.server_port}"
            origin = self.headers.get("Origin")
            if self.headers.get("Host") != host or (origin is not None and origin != f"http://{host}"):
                self.respond(403, "text/plain; charset=utf-8", b"Local dashboard only.")
            elif self.path == "/board.json":
                self.respond(200, "application/json; charset=utf-8", payload)
            elif self.path in STATIC:
                path, content_type = STATIC[self.path]
                self.respond(200, content_type, (ROOT / "public" / path).read_bytes())
            else:
                self.respond(404, "text/plain; charset=utf-8", b"Page not found.")

        do_HEAD = do_GET

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(run, port):
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    with open_server(run, port) as server:
        print(f"Open http://127.0.0.1:{server.server_port}/. Use Ctrl+C to stop.", flush=True)
        server.serve_forever()
