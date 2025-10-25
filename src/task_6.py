# src/task_spark.py
from __future__ import annotations

import queue as _q
import threading
from typing import Iterator, Optional

from pyspark.sql import SparkSession, DataFrame, functions as F, types as T

from . import domain


# ---- Public API (mirrors task_1.compute signature) ----------------------------


def compute(source: str,
           stop: threading.Event,
           *,
           processing_time: str = "1 second",
           window_duration: str = "10 seconds",
           slide_duration: str = "10 seconds",
           watermark: str = "30 seconds",
           max_files_per_trigger: int = 10
    ):
    """
    Streaming generator. Yields domain.Result objects and exits cleanly when `stop` is set.
    """

    spark = (SparkSession.builder
             .appName("task_6.compute")
             .master("local[*]")
             .config("spark.sql.session.timeZone", "UTC")
             .getOrCreate())

    outbox: _q.Queue = _q.Queue()        # thread-safe bridge to the generator

    def _foreach_batch(df, batch_id: int):
        # df should already be windowed/aggregated by your _build_stream(...)
        if df.rdd.isEmpty():
            return
        rows = df.select(
            "service", "window_start", "window_end", "total", "errors",
            (F.col("errors") / F.col("total")).alias("error_rate")
        ).collect()

        for r in rows:
            outbox.put(
                domain.Result(
                    value=float(r["error_rate"]) if r["error_rate"] is not None else 0.0,
                    newest_considered=r["window_end"],
                    oldest_considered=r["window_start"],
                )
            )

    try:
        sdf = _build_stream(
            spark,
            source,
            window_duration=window_duration,
            slide_duration=slide_duration,
            watermark=watermark,
            max_files_per_trigger=max_files_per_trigger,
        )

        query = (sdf.writeStream
                 .foreachBatch(_foreach_batch)
                 .outputMode("complete")
                 .trigger(processingTime=processing_time)
                 .start())

        # --- IMPORTANT: non-blocking drain with timeout; exit when stop && queue empty
        while True:
            if stop.is_set() and outbox.empty():
                break
            try:
                item = outbox.get(timeout=0.25)  # <- prevents blocking forever
                yield item
            except _q.Empty:
                # nothing yet; re-check stop condition
                pass

        query.stop()
        query.awaitTermination(5)

    finally:
        spark.stop()


# ---- Internals ----------------------------------------------------------------

_STATUS_RE = r"HTTP Status Code:\s*(\d+)"

# Match domain.Events TypedDict structure
_SCHEMA = T.StructType(
    [
        T.StructField("service", T.StringType(), nullable=False),
        T.StructField("timestamp", T.DoubleType(), nullable=False),  # epoch seconds
        T.StructField("message", T.StringType(), nullable=False),
    ]
)


def _build_stream(
    spark: SparkSession,
    source: str,
    *,
    window_duration: str,
    slide_duration: Optional[str],
    watermark: str,
    max_files_per_trigger: int,
) -> DataFrame:
    """
    Returns a streaming DataFrame with **windowed per-service stats** and
    precomputed columns ready for foreachBatch:
      - window_start, window_end
      - service
      - total (events)
      - errors (HTTP >= 400)
      - error_rate (errors / total)
      - avg_status
    """
    raw = (
        spark.readStream.format("json")
        .schema(_SCHEMA)
        .option("maxFilesPerTrigger", max_files_per_trigger)
        .load(source)
    )

    parsed = (
        raw.withColumn("status", F.regexp_extract("message", _STATUS_RE, 1).cast("int"))
        .withColumn("event_time", F.to_timestamp(F.from_unixtime(F.col("timestamp"))))
        .dropna(subset=["service", "status", "event_time"])
        .withColumn("is_error", (F.col("status") >= 400).cast("int"))
    )

    windowed = (
        parsed.withWatermark("event_time", watermark)
        .groupBy(
            F.window(F.col("event_time"), window_duration, slide_duration),
            F.col("service"),
        )
        .agg(
            F.count(F.lit(1)).alias("total"),
            F.sum("is_error").alias("errors"),
            F.avg("status").alias("avg_status"),
        )
        .withColumn("error_rate", (F.col("errors") / F.col("total")).cast("double"))
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "service",
            "total",
            "errors",
            "error_rate",
            "avg_status",
        )
        .orderBy(F.col("window_start").asc(), F.col("service").asc())
    )

    return windowed
