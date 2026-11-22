"""Opt-in REAL API latency harness; never run against private content by default.

Examples:
  TRANSLIFY_API_BASE=http://127.0.0.1:8000 TRANSLIFY_BENCH_TOKEN=... \
      python scripts/measure_translation_latency.py

Only the test phrases below are sent; do not publish bearer tokens or private payloads.
"""
import os
import statistics
import time
import httpx


SAMPLES = ("Hello", "Thank you very much", "Where is the train station?", "I would like a glass of water")


def main():
    base = os.environ["TRANSLIFY_API_BASE"].rstrip("/")
    token = os.environ["TRANSLIFY_BENCH_TOKEN"]
    durations = []
    with httpx.Client(timeout=60.0) as client:
        for _ in range(3):  # warm-up: excluded
            client.post(f"{base}/translate", headers={"Authorization": f"Bearer {token}"},
                        json={"text": "Hello", "source_language": "en", "target_language": "es", "store_history": False}).raise_for_status()
        for _ in range(5):
            for sample in SAMPLES:
                start = time.perf_counter()
                response = client.post(f"{base}/translate", headers={"Authorization": f"Bearer {token}"},
                    json={"text": sample, "source_language": "en", "target_language": "es", "store_history": False})
                response.raise_for_status()
                durations.append((time.perf_counter() - start) * 1000)
    durations.sort()
    p95_index = max(0, int(.95 * len(durations) + .999999) - 1)
    print(f"samples={len(durations)} p50_ms={statistics.median(durations):.1f} p95_ms={durations[p95_index]:.1f}")
    print("API round-trip measurements only. Record hardware, model state, and backend configuration separately.")


if __name__ == "__main__":
    main()
