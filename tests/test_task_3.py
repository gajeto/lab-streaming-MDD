import datetime
import json
import pathlib
import threading
import json
import numpy as np

from src import domain
from src.task_3 import compute
from unittest import assertEqual, assertAlmostEqual

"""Define the test of a sliding window algorithm that computes the rate of unsuccessful requests over the last minute
Create a series of events with timestamps and HTTP status codes,
then another series of events and compare the computed results with the expected ones.
"""

import unittest
import random

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

def test_sample_size_correct(compute, source):

    with open(source / "batch_1.json", "r") as file:
        # Test with stream larger than k
        stream_large = json.load(file)
        k = 4
        reservoir = compute(stream_large, k)
        assertEqual(len(reservoir), k, "Reservoir size should be equal to k when stream size >= k")

    with open(source / "batch_1.json", "r") as file:
        # Test with stream smaller than k
        stream_small = json.load(file)
        k_large = 10
        reservoir_small = compute(stream_small, k_large)
        assertEqual(len(reservoir_small), len(stream_small), "Reservoir size should be equal to stream size when stream size < k")

def test_uniform_probability(compute, source):
    with open(source / "batch_1.json", "r") as file:
        stream = json.load(file)
        size_stream = len(stream)
        results = []
        for k in range(1, size_stream + 1):
            reservoir = compute(stream, k)
            results.append(reservoir)
        # Calculate frequency of each element in the reservoir samples
        for reservoir in results:
            element_counts = {}
            for item in reservoir:
                item_tuple = tuple(item.items())  # Convert dict to tuple for hashing
                if item_tuple in element_counts:
                    element_counts[item_tuple] += 1
                else:
                    element_counts[item_tuple] = 1
        
        # Assert that counts are roughly equal (within a tolerance)
        expected_avg_count = 1/3 * len(results)  # Each element should appear approximately this many times
        tolerance = expected_avg_count * 0.1 # 10% tolerance
        for item, count in element_counts.items():
            assertAlmostEqual(count, expected_avg_count, delta=tolerance, message=f"Element {dict(item)} count {count} deviates from expected average {expected_avg_count}")

def test_empty_stream(self):
    stream = []
    k = 5
    reservoir = compute(stream, k)
    assertEqual(len(reservoir), 0, "Reservoir should be empty for an empty stream")
