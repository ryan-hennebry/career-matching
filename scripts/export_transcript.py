#!/usr/bin/env python3
"""Combine pre-compaction JSONL + post-compaction export into a single readable transcript."""

import json
import sys
from pathlib import Path


def extract_text_from_content(content):
    """Extract readable text from message content blocks."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            btype = block.get("type", "")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "tool_use":
                name = block.get("name", "unknown")
                inp = block.get("input", {})
                # Summarise tool calls concisely
                if name == "Bash":
                    cmd = inp.get("command", "")
                    desc = inp.get("description", "")
                    parts.append(f"[Tool: Bash] {desc}\n```\n{cmd}\n```")
                elif name == "Read":
                    parts.append(f"[Tool: Read] {inp.get('file_path', '')}")
                elif name == "Write":
                    fp = inp.get("file_path", "")
                    content_preview = inp.get("content", "")[:200]
                    parts.append(f"[Tool: Write] {fp}\n```\n{content_preview}...\n```")
                elif name == "Edit":
                    fp = inp.get("file_path", "")
                    parts.append(f"[Tool: Edit] {fp}")
                elif name == "Glob":
                    parts.append(f"[Tool: Glob] {inp.get('pattern', '')}")
                elif name == "Grep":
                    parts.append(f"[Tool: Grep] {inp.get('pattern', '')} in {inp.get('path', '.')}")
                elif name == "Task":
                    desc = inp.get("description", "")
                    agent = inp.get("subagent_type", "")
                    bg = inp.get("run_in_background", False)
                    prompt_preview = inp.get("prompt", "")[:300]
                    parts.append(f"[Tool: Task ({agent})] {desc} {'(background)' if bg else ''}\n```\n{prompt_preview}...\n```")
                elif name == "WebFetch":
                    parts.append(f"[Tool: WebFetch] {inp.get('url', '')}")
                elif name == "WebSearch":
                    parts.append(f"[Tool: WebSearch] {inp.get('query', '')}")
                elif name == "Skill":
                    parts.append(f"[Tool: Skill] {inp.get('skill', '')}")
                else:
                    parts.append(f"[Tool: {name}] {json.dumps(inp)[:200]}")
            elif btype == "tool_result":
                # Tool results in user messages
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    for rc in result_content:
                        if isinstance(rc, dict) and rc.get("type") == "text":
                            text = rc.get("text", "")
                            if len(text) > 500:
                                text = text[:500] + f"... [{len(text)} chars total]"
                            parts.append(f"[Tool Result]\n```\n{text}\n```")
                elif isinstance(result_content, str):
                    if len(result_content) > 500:
                        result_content = result_content[:500] + f"... [{len(result_content)} chars total]"
                    parts.append(f"[Tool Result]\n```\n{result_content}\n```")
    return "\n\n".join(parts)


def parse_jsonl(jsonl_path):
    """Parse JSONL into chronological conversation messages."""
    messages = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            msg_type = obj.get("type", "")
            timestamp = obj.get("timestamp", "")

            if msg_type == "user":
                content = obj.get("message", {}).get("content", "")
                text = extract_text_from_content(content)
                if text.strip():
                    messages.append({
                        "role": "user",
                        "text": text,
                        "timestamp": timestamp,
                    })
            elif msg_type == "assistant":
                content = obj.get("message", {}).get("content", [])
                text = extract_text_from_content(content)
                if text.strip():
                    messages.append({
                        "role": "assistant",
                        "text": text,
                        "timestamp": timestamp,
                    })
            elif msg_type == "system":
                # Include system messages that have readable content
                content = obj.get("message", {}).get("content", "")
                text = extract_text_from_content(content)
                if text.strip() and len(text) < 2000:
                    messages.append({
                        "role": "system",
                        "text": text,
                        "timestamp": timestamp,
                    })
    return messages


def format_transcript(messages):
    """Format messages into readable markdown."""
    lines = []
    for msg in messages:
        role = msg["role"].upper()
        ts = msg.get("timestamp", "")
        ts_str = f" ({ts})" if ts else ""

        lines.append(f"### {role}{ts_str}\n")
        lines.append(msg["text"])
        lines.append("\n---\n")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: export_transcript.py <jsonl_path> <post_compaction_export> <output_path>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    post_export = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("docs/plans/active/jsa-transcript.md")

    # Parse pre-compaction JSONL
    print(f"Parsing JSONL: {jsonl_path}")
    messages = parse_jsonl(jsonl_path)
    print(f"  Found {len(messages)} messages (user + assistant + system)")

    # Read post-compaction export
    print(f"Reading post-compaction export: {post_export}")
    post_text = post_export.read_text()

    # Combine
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("# JSA Session Transcript\n\n")
        f.write("## Part 1: Pre-Compaction (from JSONL)\n\n")
        f.write(format_transcript(messages))
        f.write("\n\n## Part 2: Post-Compaction (from /export)\n\n")
        f.write(post_text)

    size = output_path.stat().st_size
    print(f"Written: {output_path} ({size:,} bytes)")


if __name__ == "__main__":
    main()
