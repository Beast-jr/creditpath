"""Hit every official_url in the scheme KB and report HTTP status.

Run:  python -m scripts.verify_urls
Requires live internet. Not part of pytest suite.
"""

import json
import sys
import warnings
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCHEMES_DIR = Path(__file__).resolve().parent.parent / "data" / "schemes"
TIMEOUT = 10


def _get(url: str):
    """Try with SSL verification first, fall back to verify=False."""
    try:
        return requests.get(url, timeout=TIMEOUT, allow_redirects=True, verify=True)
    except requests.exceptions.SSLError:
        return requests.get(url, timeout=TIMEOUT, allow_redirects=True, verify=False)


def main() -> int:
    scheme_files = sorted(SCHEMES_DIR.glob("*.json"))
    if not scheme_files:
        print(f"ERROR: no scheme files found in {SCHEMES_DIR}")
        return 1

    passed = 0
    failed = []

    for path in scheme_files:
        data = json.loads(path.read_text())
        scheme_id = data.get("scheme_id", path.stem)
        url = data.get("official_url", "")

        try:
            resp = _get(url)
            status = resp.status_code
        except requests.RequestException as exc:
            status = str(exc)

        if status == 200:
            print(f"  PASS  {scheme_id}")
            passed += 1
        else:
            print(f"  FAIL  {scheme_id} → {url} ({status})")
            failed.append(scheme_id)

    print(f"\n{len(scheme_files)} checked, {passed} passed, {len(failed)} failed.")
    if failed:
        print("Failed:", ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
