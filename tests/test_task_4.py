import datetime
import json
import pathlib
import threading
import json
import numpy as np

from src import domain
from src.task_4 import compute
from unittest import assertEqual

def TestReservoirSampling(tmp_path: pathlib.Path):
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()

    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=10)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=20)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30)
                    ).timestamp(),
                    "message": "HTTP Status Code: 400",
                },
                 {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=10)
                    ).timestamp(),
                    "message": "HTTP Status Code: 202",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=20)
                    ).timestamp(),
                    "message": "HTTP Status Code: 503",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30)
                    ).timestamp(),
                    "message": "HTTP Status Code: 404",
                },
            ],
            file,
        )

    
def conserved_messages(compute, source) -> int:
    keep_messages = [
        "HTTP Status Code: 200",
        "HTTP Status Code: 500",
        "HTTP Status Code: 400"
    ]
    with open(source / "batch_1.json", "r") as file:
        stream = json.load(file)
        # Aproximate messages list
        filter_messages = compute(stream, keep_messages)
        """Exhaustive check of messages conserved in reservoir sampling"""
        messages_in_reservoir = [event["message"] for event in stream if event["message"] in keep_messages]
        assertEqual(filter_messages, messages_in_reservoir, "Messages should match")



