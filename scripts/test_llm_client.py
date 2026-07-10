"""Day 3 smoke test: one live Gemini call, then a cached repeat. Prints latency delta."""

import time

from core.llm.client import GeminiClient


def main() -> None:
    client = GeminiClient()
    prompt = "Reply with exactly one word: ready"

    start = time.perf_counter()
    first = client.generate(prompt)
    first_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    second = client.generate(prompt)
    second_ms = (time.perf_counter() - start) * 1000

    print(f"First call  (live):   {first_ms:8.1f} ms -> {first.strip()!r}")
    print(f"Second call (cached): {second_ms:8.1f} ms -> {second.strip()!r}")
    print(f"Speedup: {first_ms / second_ms:.0f}x faster from cache")

    assert first == second, "Cached response should match the live one"
    assert second_ms < first_ms, "Cached call should be faster than live call"
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()