import datetime
import json
import pathlib
import random
import threading
import time
from collections import Counter
from queue import Queue
from typing import Any, Dict, Iterator, List, Optional

from . import domain

def compute(source: str, stop: threading.Event, **kwargs: Any) -> Iterator[domain.Result]:
    
    k = int(kwargs.get('k', 64))
    seed = int(kwargs.get('random_seed', 42))
    random.seed(int(seed))

    q = Queue()

    threading.Thread(target=producer, args=(source, stop, q), daemon=True).start()

    reservoir: List[Dict] = []
    class_count: Counter = Counter()

    # Window timestamp limits
    min_ts_seen: Optional[float] = None
    max_ts_seen: Optional[float] = None

    # Total number of elements seen so far
    n_seen = 0

    while not stop.is_set():
        batch = q.get(timeout=0.25)
        
        if isinstance(batch, dict):
            batch = [batch]
        
        events = [e for e in batch if isinstance(e, dict) and 'timestamp' in e and 'message' in e]
        if not events and n_seen == 0:
            q.task_done()
            continue

        for e in events:
            ts = float(e['timestamp'])
            msg = e.get('message', '')
            code = int(msg.split('HTTP Status Code:')[-1].strip()) if 'HTTP Status Code:' in msg else None
            if code is None:
                min_ts_seen = ts if min_ts_seen is None else min(min_ts_seen, ts)
                max_ts_seen = ts if max_ts_seen is None else max(max_ts_seen, ts)
                n_seen += 1
                continue

            # Update global ts bounds
            min_ts_seen = ts if min_ts_seen is None else min(min_ts_seen, ts)
            max_ts_seen = ts if max_ts_seen is None else max(max_ts_seen, ts)

            # reservoir sampling
            if len(reservoir) < k:
                reservoir.append({'code': code, 'timestamp': ts})
                class_count[code] += 1
            else:
                j = random.randint(0, n_seen)  # inclusive
                if j < k:
                    old_code = reservoir[j]['code']
                    if old_code in class_count:
                        class_count[old_code] -= 1
                        if class_count[old_code] <= 0:
                            del class_count[old_code]
                    reservoir[j] = {'code': code, 'timestamp': ts}
                    class_count[code] += 1

            n_seen += 1

        # If there is no sampling, stop streaming
        if not reservoir or min_ts_seen is None or max_ts_seen is None:
            q.task_done()
            continue

        # In multimodal case select smallest code
        max_count = max(class_count.values())
        candidates = [c for c, cnt in class_count.items() if cnt == max_count]
        mode_code = min(candidates)

        yield domain.Result(
            value=float(mode_code),
            newest_considered=datetime.datetime.fromtimestamp(max_ts_seen),
            oldest_considered=datetime.datetime.fromtimestamp(min_ts_seen),
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
