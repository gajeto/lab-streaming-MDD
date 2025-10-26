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
        

def producer (source: str, stop: threading.Event, queue: Any) -> None:
    path = pathlib.Path(source)
    seen = set[str]()
    lock = threading.Lock()

    while not stop.is_set():
        for file in path.glob('*.json'):

            if file.name in seen:
                continue

            with lock:
                if file.name in seen:
                    continue
                seen.add(file.name)

            with open(file) as f:
                data = json.load(f)

            if isinstance(data, dict):
                data = [data]

            queue.put(data)

        time.sleep(1)  # Avoid busy waiting