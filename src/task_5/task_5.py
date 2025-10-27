import datetime
import json
import pathlib
import threading
import time
from queue import Queue
from typing import Any, Iterator, Optional, List

import polars as pl

from src import domain


def _process_stream(path: pathlib.Path) -> Optional[domain.Result]:
    # Polars LazyFrame scan with streaming
    lf = pl.scan_ndjson(str(path), infer_schema_length=1000)

    # Ensure required columns exist
    lf = lf.select(
        [
            pl.col('timestamp').cast(pl.Float64, strict=False).alias('timestamp'),
            pl.col('message').cast(pl.Utf8, strict=False).alias('message'),
        ]
    ).drop_nulls(['timestamp', 'message'])

    # Define unsuccessful events
    lf = lf.with_columns(
        pl.when(pl.col('message').str.contains('HTTP Status Code: 200'))
        .then(pl.lit(0, dtype=pl.Int64))
        .otherwise(pl.lit(1, dtype=pl.Int64))
        .alias('unsuccessful')
    )

    # Aggregate in streaming mode
    out = (
        lf.select(
            [
                pl.len().alias('total'),
                pl.col('unsuccessful').sum().alias('unsuccessful'),
                pl.col('timestamp').min().alias('min_ts'),
                pl.col('timestamp').max().alias('max_ts'),
            ]
        )
        .collect(streaming=True)
    )

    if out.height == 0:
        return None

    total = int(out['total'][0])
    if total == 0:
        return None

    unsuccessful = int(out['unsuccessful'][0])
    min_ts = float(out['min_ts'][0])
    max_ts = float(out['max_ts'][0])

    value = unsuccessful / total

    return domain.Result(
        value=value,
        newest_considered=datetime.datetime.fromtimestamp(max_ts),
        oldest_considered=datetime.datetime.fromtimestamp(min_ts),
    )


def compute(source: str, stop: threading.Event, **_: Any) -> Iterator[domain.Result]:
    q = Queue()
    
    producer_thread = threading.Thread(target=producer, args=(source, stop, q), daemon=True)
    producer_thread.start()

    while not stop.is_set():
        file_path = q.get()
        result = _process_stream(pathlib.Path(file_path))
        if result is not None:
            yield result

        q.task_done()


def producer(source: str, stop: threading.Event, queue: Queue) -> None:
    src = pathlib.Path(source)
    seen = set()
    patterns = ("*.ndjson", "*.jsonl")

    while not stop.is_set():
        files: List[pathlib.Path] = []
        for pat in patterns:
            files.extend(sorted(src.glob(pat)))
        for f in files:
            if f.name in seen:
                continue
            seen.add(f.name)
            queue.put(str(f))
        time.sleep(0.05)
