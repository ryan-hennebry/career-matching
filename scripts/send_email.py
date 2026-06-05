#!/usr/bin/env python3
"""Send email via Resend API with HTML body from file and optional attachments."""

import argparse
import base64
import os
import sys
from pathlib import Path


def load_dotenv():
    """Load .env from parent directory if it exists.

    Note: Uses setdefault — existing shell env vars take precedence over .env values.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key.strip(), value)


def main():
    load_dotenv()

    try:
        import resend
    except ImportError:
        print("Error: resend not installed. Run: pip install resend", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Send email via Resend API")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True, help="Path to HTML file for email body")
    parser.add_argument("--attachment", default=None, help="Path to file attachment")
    args = parser.parse_args()

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    resend.api_key = api_key

    with open(args.body_file, encoding="utf-8") as f:
        html_body = f.read()

    params = {
        "from": "Job Search Agent <onboarding@resend.dev>",
        "to": [args.to],
        "subject": args.subject,
        "html": html_body,
    }

    if args.attachment:
        if not os.path.exists(args.attachment):
            print(f"Error: Attachment not found: {args.attachment}", file=sys.stderr)
            sys.exit(1)
        with open(args.attachment, "rb") as f:
            raw = f.read()
        content = base64.b64encode(raw).decode("utf-8")
        params["attachments"] = [{"filename": os.path.basename(args.attachment), "content": content}]

    try:
        result = resend.Emails.send(params)
        print(f"Email sent. ID: {result['id']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
