from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Send DGT board events to Sentinel.")
    parser.add_argument("--api-base", required=True, help="Sentinel API base URL, e.g. http://localhost:8000")
    parser.add_argument("--event-id", required=True, help="Event ID")
    parser.add_argument("--session-id", default=None, help="Live session ID (optional)")
    parser.add_argument("--board-serial", default=None, help="DGT board serial (optional)")
    parser.add_argument("--stdin-json", action="store_true", help="Read DGT events as JSON lines from stdin")
    parser.add_argument("--x-role", default="system_admin", help="Sentinel role header")
    args = parser.parse_args()

    if not args.stdin_json:
        print("This bridge expects JSON lines on stdin. Use --stdin-json.", file=sys.stderr)
        return 2

    url = args.api_base.rstrip("/") + "/v1/otb/board-events"
    headers = {"Content-Type": "application/json", "X-Role": args.x_role}

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue
        body = {
            "event_id": args.event_id,
            "session_id": args.session_id,
            "board_serial": args.board_serial,
            "move_uci": payload.get("move_uci"),
            "ply": payload.get("ply"),
            "fen": payload.get("fen"),
            "clock_ms": payload.get("clock_ms"),
            "raw": payload,
        }
        try:
            requests.post(url, headers=headers, json=body, timeout=5)
        except Exception:
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
