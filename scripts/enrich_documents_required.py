"""
scripts/enrich_documents_required.py
Adds documents_required field to each scheme JSON using Gemini.
Calls API directly (bypasses GeminiClient 15s timeout).
Usage: PYTHONPATH=. python scripts/enrich_documents_required.py
"""

import json
import time
import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

SCHEMES_DIR = Path("data/schemes")

PROMPT_TEMPLATE = """You are an expert on Indian government financing schemes for MSMEs.

For the scheme below, list the documents typically required when applying.
Base your answer on official RBI, SIDBI, and government guidelines.

Scheme name: {name}
Administered by: {administered_by}
Scheme type: {scheme_type}
Description: {retrieval_text}
Official URL: {official_url}

Return ONLY a JSON array of strings. No explanation, no markdown, no preamble.
Each string is one required document. Be specific (e.g. "Udyam Registration Certificate" not "registration proof").
Maximum 12 items.

Example output format:
["Udyam Registration Certificate", "PAN Card", "Bank statements (6 months)", "Business address proof"]
"""


def enrich_scheme(path: Path) -> bool:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)

    if "documents_required" in doc:
        print(f"  SKIP (already enriched): {path.name}")
        return False

    prompt = PROMPT_TEMPLATE.format(
        name=doc.get("name", ""),
        administered_by=doc.get("administered_by", ""),
        scheme_type=doc.get("scheme_type", ""),
        retrieval_text=doc.get("retrieval_text", ""),
        official_url=doc.get("official_url", ""),
    )

    try:
        response = model.generate_content(
            prompt,
            request_options={"timeout": 60},  # 60s timeout
        )
        raw = response.text.strip()
    except Exception as e:
        if "429" in str(e):
            print(f"  QUOTA EXHAUSTED at {path.name}. Stopping. Re-run tomorrow to continue.")
            raise SystemExit(0)
        print(f"  ERROR calling API for {path.name}: {e}")
        return False

    # strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    try:
        documents = json.loads(raw)
        if not isinstance(documents, list):
            raise ValueError("Not a list")
    except Exception as e:
        print(f"  ERROR parsing response for {path.name}: {e}")
        print(f"  Raw: {raw[:200]}")
        return False

    doc["documents_required"] = documents

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"  OK ({len(documents)} docs): {path.name}")
    return True


if __name__ == "__main__":
    paths = sorted(SCHEMES_DIR.glob("*.json"))
    print(f"Enriching {len(paths)} scheme files...\n")

    enriched = failed = skipped = 0

    for path in paths:
        result = enrich_scheme(path)
        if result:
            enriched += 1
        else:
            with open(path) as f:
                d = json.load(f)
            if "documents_required" in d:
                skipped += 1
            else:
                failed += 1
        time.sleep(2)

    print(f"\nDone. Enriched: {enriched}, Skipped: {skipped}, Failed: {failed}")