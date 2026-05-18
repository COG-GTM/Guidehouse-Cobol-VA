#!/usr/bin/env python3
"""Create a cloud Devin session from a prompt file using DEVIN_API_KEY.

This helper intentionally reads the API key from the environment and never prints it.
It uses the legacy v1 sessions API because the current local key is a personal
`apk_user_...` key scoped to the US Federal org.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.devin.ai/v1/sessions"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: scripts/create_devin_session.py <prompt-file>", file=sys.stderr)
        return 2

    api_key = os.environ.get("DEVIN_API_KEY")
    if not api_key:
        print("DEVIN_API_KEY is not set", file=sys.stderr)
        return 2

    prompt_path = Path(sys.argv[1])
    prompt = prompt_path.read_text().strip()
    if not prompt:
        print(f"Prompt file is empty: {prompt_path}", file=sys.stderr)
        return 2

    payload = json.dumps({"prompt": prompt, "idempotent": False}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Devin API error {exc.code}: {body}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2, sort_keys=True))
    if data.get("url"):
        print(f"\nOpen: {data['url']}")
    elif data.get("session_url"):
        print(f"\nOpen: {data['session_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
