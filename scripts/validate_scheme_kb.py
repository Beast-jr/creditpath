"""Validate every scheme JSON under data/schemes/ against data/scheme_schema.json.

Run: python -m scripts.validate_scheme_kb
Exit code 0 if all pass, 1 if any fail (usable in CI / pre-commit).
"""

import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path("data/scheme_schema.json")
SCHEMES_DIR = Path("data/schemes")


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def find_scheme_files() -> list[Path]:
    """All *.json under data/schemes/, sorted for stable output."""
    return sorted(SCHEMES_DIR.rglob("*.json"))


def validate_file(path: Path, validator: jsonschema.Draft7Validator) -> list[str]:
    """Return a list of error strings for one file. Empty list means PASS."""
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        field = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"[{field}] {err.message}")
    return errors


def main() -> int:
    schema = load_schema()
    validator = jsonschema.Draft7Validator(schema)
    files = find_scheme_files()

    if not files:
        print("No scheme files found under data/schemes/ (nothing to validate yet).")
        return 0

    total_fail = 0
    for path in files:
        errors = validate_file(path, validator)
        if errors:
            total_fail += 1
            print(f"FAIL  {path}")
            for e in errors:
                print(f"        {e}")
        else:
            print(f"PASS  {path}")

    print(f"\n{len(files) - total_fail}/{len(files)} passed.")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())