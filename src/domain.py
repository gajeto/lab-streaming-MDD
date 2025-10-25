import datetime
from typing import NamedTuple, TypedDict


class Result(NamedTuple):
    value: float
    newest_considered: datetime.datetime
    oldest_considered: datetime.datetime

class Events(TypedDict):
    service: str
    timestamp: float
    message: str
