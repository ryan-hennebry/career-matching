"""Shared response helpers for Vercel serverless functions.

Centralizes CORS headers and JSON response boilerplate used by all 8 endpoints.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler


def json_response(handler: BaseHTTPRequestHandler, data: dict, status: int = 200) -> None:
    """Send a JSON response with CORS headers."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())


def cors_preflight(handler: BaseHTTPRequestHandler) -> None:
    """Handle CORS OPTIONS preflight request."""
    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
