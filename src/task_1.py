import datetime
import json
import pathlib
import threading
import queue
from typing import Any, Iterator
import time
import requests

from . import domain
"""Here we want to compute the rate of unccessful requests over a queue of events.
We will read events from JSON files in a given directory, process them in batches,
and yield the computed rate along with the timestamps of the newest and oldest events considered in each batch.
"""

def compute(source: str, stop: threading.Event, **_: Any) -> Iterator[domain.Result]:

    q = threading.Queue()

    producer_thread = threading.Thread(target=producer, args=(source, q, stop))
    producer_thread.start()

    count = 0
    count_2xx = 0
    while not stop.is_set():
        batch = q.get()
        for e in batch:
            count += 1
            message = e["message"]
            code = message.split(": ")[-1]
            if code.startswith("2"):
                count_2xx += 1
        q.task_done()
        yield domain.Result(
            value=count_2xx / count if count > 0 else 0.0,
            newest_considered=datetime.datetime.fromtimestamp(
                max(e["timestamp"] for e in batch)
            ),
            oldest_considered=datetime.datetime.fromtimestamp(
                min(e["timestamp"] for e in batch)
            ),
        ) 
        


def producer (source: str, stop: threading.Event, queue: threading.Queue) -> None:
    path = pathlib.Path(source)
    seen = set[str]()
    lock = threading.Lock()

    while not stop.is_set():
        for file in path.glob("*.json"):

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