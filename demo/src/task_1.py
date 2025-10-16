import datetime
import json
import pathlib
import threading
from typing import Any, Iterator

from . import domain


def compute(source: str, **_: Any) -> Iterator[domain.Result]:
    import random
    import time

    while True:
        time.sleep(1)
        yield domain.Result(
            value=random.random(),
            newest_considered=datetime.datetime.now(),
            oldest_considered=datetime.datetime.now(),
        )
