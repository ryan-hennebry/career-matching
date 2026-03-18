#!/usr/bin/env python3
"""Check HTML for prohibited colors in CSS contexts. Constants inlined (single consumer)."""
from __future__ import annotations
import re
import sys
from pathlib import Path

PROHIBITED_NAMED = ["red", "blue", "orange", "amber"]
PROHIBITED_HEX = [
    "#0000ff", "#007bff", "#2563eb", "#3b82f6", "#1d4ed8", "#60a5fa", "#93c5fd",
    "#ff0000", "#dc2626", "#ef4444", "#b91c1c", "#f87171", "#fca5a5",
    "#f59e0b", "#d97706", "#fbbf24", "#92400e",
    "#f97316", "#ea580c", "#fb923c", "#c2410c",
]

def verify_html(filepath: str) -> list[str]:
    html = Path(filepath).read_text(encoding="utf-8")
    css_parts = [m.group(1) for m in re.finditer(r'style\s*=\s*["\']([^"\']*)["\']', html, re.I)]
    css_parts += [m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)]
    css = "\n".join(css_parts).lower()
    violations = []
    for name in PROHIBITED_NAMED:
        if re.search(rf":\s*[^;]*\b{name}\b", css, re.I):
            violations.append(f"Prohibited named color: {name}")
    for hx in PROHIBITED_HEX:
        if hx.lower() in css:
            violations.append(f"Prohibited hex color: {hx}")
    return violations

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_html.py <html_file>", file=sys.stderr)
        sys.exit(2)
    vs = verify_html(sys.argv[1])
    if vs:
        for v in vs:
            print(v, file=sys.stderr)
        sys.exit(1)
