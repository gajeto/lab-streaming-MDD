import datetime
import json
import pathlib
import threading
from queue import Queue
from typing import Any, Iterator
import time
import requests

from . import domain

def compute(source: str, stop: threading.Event, **_: Any) -> Iterator[domain.Result]:

    q = Queue()

    producer_thread = threading.Thread(target=producer, args=(source, stop, q), daemon=True)
    producer_thread.start()

    events: list[dict] = []
    count_total = 0
    count_2xx = 0

    while not stop.is_set():
        batch = q.get()
        if isinstance(batch, dict):
            batch = [batch]
        
        events.extend(batch)
        for e in batch:
            count_total += 1
            msg = e.get('message', '')
            code = msg.split(': ')[-1] if ': ' in msg else msg
            if code.startswith('2'):
                count_2xx += 1
        
        newest_ts = max(e['timestamp'] for e in events)
        oldest_ts = min(e['timestamp'] for e in events)

        yield domain.Result(
            value=(count_2xx / count_total) if count_total else 0.0,
            newest_considered=datetime.datetime.fromtimestamp(newest_ts),
            oldest_considered=datetime.datetime.fromtimestamp(oldest_ts),
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