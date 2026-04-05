"""Log in to Garmin interactively and print base64 garth tokens.

Run locally (where Garmin isn't blocking you), then upload to production:

    cd apps/sync
    uv run python -m app.scripts.garmin_export_tokens

    # Then upload to prod:
    curl -X POST https://YOUR_SERVER/api/sync/garmin-tokens \
         -H 'Content-Type: application/json' \
         -d '{"tokens": "<paste output here>"}'
"""

import os
import sys

from garminconnect import Garmin


def main():
    email = os.environ.get("GARMIN_EMAIL") or input("Garmin email: ")
    password = os.environ.get("GARMIN_PASSWORD") or input("Garmin password: ")

    client = Garmin(email, password)
    print("Logging in to Garmin Connect...")
    client.login()

    tokens = client.garth.dumps()
    print("\n--- Copy everything below this line ---")
    print(tokens)
    print("--- Copy everything above this line ---")
    print(f"\nToken length: {len(tokens)} chars")


if __name__ == "__main__":
    main()
