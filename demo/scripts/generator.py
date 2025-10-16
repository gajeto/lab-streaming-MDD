#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3",
# ]
# ///


import concurrent.futures
import datetime
import json
import pathlib
import random
import time
import uuid
from typing import Any, Callable, Iterator

import boto3

type Event = dict[str, Any] | list[dict[str, Any]]
type Writer = Callable[[Event], None]


def main(
    num_files: int,
    events_per_batch: int,
    batch_delay: int,
    writer: Writer,
) -> None:
    event_generator = _generate_random_events(events_per_batch)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for _ in range(num_files):
            time.sleep(batch_delay)
            event = next(event_generator)
            executor.submit(writer, event)


class _LocalWriter:
    def __init__(self, dir: pathlib.Path):
        self._dir = dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: Event) -> None:
        payload = json.dumps(event)
        name = _generate_name()
        print(f"writing {name}")
        with open(self._dir / name, "w") as file:
            file.write(payload)


class _S3Writer:
    def __init__(self, path: str):
        *_, self._bucket, self._prefix = path.split("/", 3)
        self._s3 = boto3.client("s3")
        self._s3.create_bucket(Bucket=self._bucket)

    def __call__(self, event: Event) -> None:
        payload = json.dumps(event)
        name = _generate_name()
        print(f"writing {name}")
        self._s3.put_object(
            Bucket=self._bucket, Key=f"{self._prefix}/{name}", Body=payload
        )

def _generate_name() -> str:
    now = datetime.datetime.now()
    return f"{now.strftime('%Y%m%d_%H%M%S_%f')}.json"


def _generate_random_events(events_per_batch: int) -> Iterator[Event]:
    random.seed(a=42)
    statuses = [200, 201, 202, 203, 400, 401, 402, 403, 404, 500]
    services = ["training", "evaluation", "inference", "monitoring"]
    now = datetime.datetime.now()
    while True:
        status_code = random.choice(statuses)
        now += datetime.timedelta(seconds=random.randint(-100, 300))
        batch = [
            {
                "service": random.choice(services),
                "timestamp": now.timestamp(),
                "message": f"HTTP Status Code: {status_code}",
            }
            for _ in range(events_per_batch)
        ]
        yield batch


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        help="Output path for the data, could be a local directory or a bucket, specify with the --is-bucket flag",
    )
    parser.add_argument(
        "--is-bucket", action="store_true", help="Whether the output is a bucket"
    )
    parser.add_argument(
        "--num-files",
        default=10,
        type=int,
        help="Number of files to generate in the output directory",
    )
    parser.add_argument(
        "--events-per-batch",
        default=10,
        type=int,
        help="Number of events to generate in each batch",
    )
    parser.add_argument(
        "--batch-delay",
        default=1,
        type=int,
        help="Delay between batches in seconds",
    )
    args = parser.parse_args()

    writer: Writer
    if args.is_bucket:
        writer = _S3Writer(args.output)
    else:
        writer = _LocalWriter(pathlib.Path(args.output))

    main(args.num_files, args.events_per_batch, args.batch_delay, writer)
