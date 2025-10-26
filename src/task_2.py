import datetime
import json
import pathlib
import threading
from queue import Queue
from typing import Any, Iterator, List, Dict
import time

from . import domain

def compute(source: str, stop: threading.Event, **_: Any) -> Iterator[domain.Result]:
    q = Queue()
    
    threading.Thread(target=producer, args=(source, stop, q), daemon=True).start()

    events: List[Dict] = []
    while not stop.is_set():
        try:
            batch = q.get(timeout=0.25)
        except Exception:
            continue

        if batch is None:
            break

        if isinstance(batch, dict):
            batch = [batch]
        batch = [e for e in batch if isinstance(e, dict) and ('timestamp' in e)]

        if not batch and not events:
            q.task_done()
            continue

        # Accumulate then prune to last minute relative to current newest timestamp
        events.extend(batch)
        if events:
            newest_ts = max(e['timestamp'] for e in events)
            cutoff = newest_ts - 60 # window of 10 seconds
            events = [e for e in events if e['timestamp'] >= cutoff]

        if not events:
            q.task_done()
            continue

        newest_ts = max(e['timestamp'] for e in events)
        oldest_ts = min(e['timestamp'] for e in events)

        total = len(events)
        unsuccessful = sum(
            1 for e in events
            if "HTTP Status Code: 200" not in e.get('message', '')
        )
        value = unsuccessful / total if total else 0.0

        yield domain.Result(
            value=value,
            newest_considered=datetime.datetime.fromtimestamp(newest_ts),
            oldest_considered=datetime.datetime.fromtimestamp(oldest_ts),
        )

        q.task_done()

def producer(source: str, stop: threading.Event, queue: Queue) -> None:
   
    seen = set()
    src = pathlib.Path(source)
    while not stop.is_set():
        for file in sorted(src.glob("*.json")):
            if file.name in seen:
                continue
            seen.add(file.name)

            with open(file, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data = [data]

            queue.put(data)

        time.sleep(0.05)
