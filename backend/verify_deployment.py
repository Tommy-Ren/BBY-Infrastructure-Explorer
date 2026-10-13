"""Trigger the data deploy hook and require the production API to serve this export."""

import json
import os
from pathlib import Path
import time

import requests


def main():
    hook = os.environ["VERCEL_DATA_DEPLOY_HOOK"]
    # Do not include the secret URL in errors or log response bodies.
    try:
        response = requests.post(hook, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        raise SystemExit("Vercel deploy hook failed; inspect the deployment dashboard") from None
    expected = json.loads((Path(__file__).parent / "data/manifest.json").read_text())["dataset_version"]
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        try:
            response = requests.get(
                "https://bby-infrastructure-explorer.vercel.app/api/v1/datasets/current",
                headers={"Cache-Control": "no-cache"}, timeout=20,
            )
            response.raise_for_status()
            if response.json()["dataset_version"] == expected:
                print(f"Production now serves {expected}")
                return
        except (requests.RequestException, ValueError, KeyError):
            pass
        time.sleep(15)
    raise SystemExit(f"Production did not publish {expected} within 10 minutes")


if __name__ == "__main__":
    main()
