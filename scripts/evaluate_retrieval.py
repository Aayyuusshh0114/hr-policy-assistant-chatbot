import argparse
import json
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against a labelled JSON set.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text())
    hits = 0
    with httpx.Client(base_url=args.base_url, timeout=30) as client:
        for case in cases:
            response = client.post("/api/search", json={"query": case["question"], "k": 3})
            response.raise_for_status()
            sources = [item["filename"] for item in response.json()["results"]]
            hit = case["expected_source"] in sources
            hits += int(hit)
            print(f"{'PASS' if hit else 'FAIL'} {case['question']} -> {sources}")
    print(f"Hit@3: {hits / len(cases):.3f} ({hits}/{len(cases)})")


if __name__ == "__main__":
    main()

