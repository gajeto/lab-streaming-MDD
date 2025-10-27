import datetime
import json
import pathlib
import threading
import time
from queue import Queue
from typing import Any, Dict, Iterator, List, Optional
from bloom_filter2 import BloomFilter

from . import domain

def _load_bloom_with_file(path: pathlib.Path, capacity: int = 1_000_000, error_rate: float = 0.001):
    bf = BloomFilter(max_elements=capacity, error_rate=error_rate)  
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            msg = line.strip()
            if msg:
                bf.add(msg)
    return bf


def compute(source: str, stop: threading.Event, **kwargs: Any) -> Iterator[domain.Result]:
    interest_file = kwargs.get('interest_file')
    file = pathlib.Path(interest_file)
  
    capacity = int(kwargs.get('capacity', 1_000_000))
    error_rate = float(kwargs.get('error_rate', 0.001))

    bloom = _load_bloom_with_file(file, capacity=capacity, error_rate=error_rate)

    q: Queue = Queue()
    threading.Thread(target=producer, args=(source, stop, q), daemon=True).start()

    forwarded = 0
    total = 0
    min_ts: Optional[float] = None
    max_ts: Optional[float] = None

    while not stop.is_set():
        try:
            batch = q.get(timeout=0.25)
        except Exception:
            continue

        if batch is None:
            break

        # Normalize -> list of dicts
        if isinstance(batch, dict):
            batch = [batch]
        events: List[Dict] = [
            e for e in batch
            if isinstance(e, dict) and 'timestamp' in e and 'message' in e
        ]

        if not events and total == 0:
            q.task_done()
            continue

        for e in events:
            ts = float(e['timestamp'])
            msg = str(e['message'])

            # Update bounds
            min_ts = ts if min_ts is None else min(min_ts, ts)
            max_ts = ts if max_ts is None else max(max_ts, ts)

            # Forwarding decision via Bloom
            total += 1
            if msg in bloom:
                forwarded += 1
                print('Forwarded message:', msg)

        if total == 0 or min_ts is None or max_ts is None:
            q.task_done()
            continue

        yield domain.Result(
            value=forwarded / total,
            newest_considered=datetime.datetime.fromtimestamp(max_ts),
            oldest_considered=datetime.datetime.fromtimestamp(min_ts),
        )

        q.task_done()


def producer(source: str, stop: threading.Event, queue: Queue) -> None:
    seen = set()
    src = pathlib.Path(source)

    while not stop.is_set():
        for file in sorted(src.glob('*.json')):
            if file.name in seen:
                continue
            seen.add(file.name)

            with open(file, 'r') as f:
                data = json.load(f)

            batch = data if isinstance(data, list) else [data]
            queue.put(batch)

        time.sleep(0.05)
