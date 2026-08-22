from __future__ import annotations

import argparse
import sys
import time

import httpx

sys.path.insert(0, ".")
from simulator.event_generator import generate_event_batch


def send_batch(
    api_url: str,
    batch_size: int,
    verbose: bool = True,
) -> dict:
    events = generate_event_batch(batch_size)

    payload = {
        "events": [
            {
                "id": e.id,
                "source": e.source.value,
                "title": e.title,
                "severity": e.severity.value,
                "timestamp": e.timestamp.isoformat(),
                "region": e.region,
                "service": e.service,
                "metadata": e.metadata,
            }
            for e in events
        ]
    }

    if verbose:
        print(f"\n[>>] Sending batch of {len(events)} events to {api_url}")
        for ev in events:
            print(f"   - [{ev.severity.value:>8}] [{ev.source.value:>16}] {ev.title[:70]}")

    resp = httpx.post(api_url, json=payload, timeout=10.0)
    resp.raise_for_status()
    result = resp.json()

    if verbose:
        print(f"[OK] Server response: {result['message']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="GlanceApp 93 Event Stream Sender")
    parser.add_argument("--url", default="http://localhost:8000/api/events/ingest",
                        help="Ingest API URL")
    parser.add_argument("--batch-size", type=int, default=15,
                        help="Number of events per batch")
    parser.add_argument("--rounds", type=int, default=3,
                        help="Number of batches to send")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Seconds between batches")
    args = parser.parse_args()

    print(f"Sending to: {args.url}")
    print(f"Batch size: {args.batch_size} | Rounds: {args.rounds} | Interval: {args.interval}s")

    total_sent = 0
    for i in range(args.rounds):
        print(f"\n--- Round {i + 1}/{args.rounds} ---")
        try:
            send_batch(args.url, args.batch_size)
            total_sent += args.batch_size
        except httpx.HTTPError as e:
            print(f"[ERROR] Error sending batch: {e}")
            continue

        if i < args.rounds - 1:
            time.sleep(args.interval)

    print(f"\nCompleted: Sent {total_sent} events across {args.rounds} rounds.")


if __name__ == "__main__":
    main()
