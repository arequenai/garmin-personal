"""Convert Garmin Connect browser tokens into garth-compatible format.

Usage:
    cd apps/sync

    # Paste interactively:
    uv run python -m app.scripts.garmin_import_browser_tokens

    # Or pipe from a file:
    uv run python -m app.scripts.garmin_import_browser_tokens < token.json

    # Then upload to production:
    curl -X POST https://YOUR_SERVER/api/sync/garmin-tokens \
         -H "Content-Type: application/json" \
         -d '{"tokens": "<paste output>"}'

How to get the token JSON:
    1. Log into connect.garmin.com in Chrome
    2. F12 → Application → Local Storage → connect.garmin.com
    3. Click on the "token" entry, copy the full JSON value
"""

import base64
import json
import sys


def main():
    print("Paste the token JSON from Chrome Local Storage, then press Enter:")
    print("(on Windows: paste, then press Enter twice or Ctrl+Z then Enter)")
    print()

    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except EOFError:
        pass

    raw = "".join(lines).strip()
    if not raw:
        print("ERROR: No input received", file=sys.stderr)
        sys.exit(1)

    try:
        browser_token = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if "access_token" not in browser_token:
        print("ERROR: JSON missing 'access_token' field", file=sys.stderr)
        sys.exit(1)

    # Convert browser timestamp (ms) to seconds for garth
    expires_at = int(browser_token.get("expires", 0)) // 1000
    refresh_expires_at = int(browser_token.get("refresh_token_expires", 0)) // 1000

    # Construct garth-compatible token store
    garth_data = {
        "oauth1_token": None,
        "oauth2_token": {
            "scope": browser_token.get("scope", ""),
            "jti": browser_token.get("jti", ""),
            "access_token": browser_token["access_token"],
            "token_type": browser_token.get("token_type", "Bearer"),
            "expires_in": int(browser_token.get("expires_in", 300)),
            "expires_at": expires_at,
            "refresh_token": browser_token.get("refresh_token", ""),
            "refresh_token_expires_in": int(
                browser_token.get("refresh_token_expires_in", 7200)
            ),
            "refresh_token_expires_at": refresh_expires_at,
        },
        "domain": "garmin.com",
    }

    token_store = base64.b64encode(json.dumps(garth_data).encode()).decode()

    print()
    print("--- GARTH TOKEN STORE (copy everything below) ---")
    print(token_store)
    print("--- END ---")
    print()
    print(f"Length: {len(token_store)} chars")
    print()
    print("IMPORTANT: These tokens expire in ~2 hours.")
    print("After uploading, immediately trigger a sync so the server")
    print("refreshes and persists new tokens.")


if __name__ == "__main__":
    main()
