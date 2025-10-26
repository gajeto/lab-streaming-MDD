from __future__ import annotations

import queue as _q
import threading
from typing import Optional
from pyspark.sql import SparkSession, DataFrame, functions as F, types as T

from src import domain

def compute(source: str,
           stop: threading.Event,
           *,
           checkpoint: str,
           processing_time: str = '1 second',
           window_duration: str = '10 seconds',
           slide_duration: str = '10 seconds',
           watermark: str = '30 seconds',
           max_files_per_trigger: int = 10
    ):
    #master = os.getenv('SPARK_MASTER', 'local[*]')
    spark = (SparkSession.builder
             .appName('task_6.compute')
             .config('spark.sql.session.timeZone', 'UTC')
             .getOrCreate())

    outbox: _q.Queue = _q.Queue()        # thread-safe with the generator

    def _foreach_batch(df, batch_id):
        if df.rdd.isEmpty():
            return
        rows = df.select(
            'service', 'window_start', 'window_end', 'total', 'errors',
            (F.col('errors') / F.col('total')).alias('error_rate')
        ).collect()

        for r in rows:
            outbox.put(
                domain.Result(
                    value=float(r['error_rate']) if r['error_rate'] is not None else 0.0,
                    newest_considered=r['window_end'],
                    oldest_considered=r['window_start'],
                )
            )

    try:
        sdf = producer(
            spark,
            source,
            window_duration=window_duration,
            slide_duration=slide_duration,
            watermark=watermark,
            max_files_per_trigger=max_files_per_trigger,
        )

        query = (sdf.writeStream
                 .foreachBatch(_foreach_batch)
                 .outputMode('complete')
                 .option('checkpointLocation', checkpoint)
                 .trigger(processingTime=processing_time)
                 .start())

        # Non-blocking drain with timeout
        while True:
            if stop.is_set() and outbox.empty():
                break
            try:
                item = outbox.get(timeout=0.25)  # prevents blocking forever
                yield item
            except _q.Empty:
                pass

        query.stop()
        query.awaitTermination(5)

    finally:
        spark.stop()

# Regular expression to extract HTTP status code from message
_STATUS_RE = r'HTTP Status Code:\s*(\d+)'

# Match domain.Events TypedDict structure
_SCHEMA = T.StructType(
    [
        T.StructField('service', T.StringType(), nullable=False),
        T.StructField('timestamp', T.DoubleType(), nullable=False),  # epoch seconds
        T.StructField('message', T.StringType(), nullable=False),
    ]
)

def producer(
    spark: SparkSession,
    source: str,
    *,
    window_duration: str,
    slide_duration: Optional[str],
    watermark: str,
    max_files_per_trigger: int,
) -> DataFrame:
    raw = (
        spark.readStream.format('json')
        .schema(_SCHEMA)
        .option('maxFilesPerTrigger', max_files_per_trigger)
        .option('pathGlobFilter', '*.json')
        .option('recursiveFileLookup', 'true')
        .load(source)
    )

    parsed = (
        raw.withColumn('status', F.regexp_extract('message', _STATUS_RE, 1).cast('int'))
        .withColumn('event_time', F.to_timestamp(F.from_unixtime(F.col('timestamp'))))
        .dropna(subset=['service', 'status', 'event_time'])
        .withColumn('is_error', (F.col('status') >= 400).cast('int')) # 1 if status errored (HTTP >= 400), else 0
    )

    windowed = (
        parsed.withWatermark('event_time', watermark)
        .groupBy(
            F.window(F.col('event_time'), window_duration, slide_duration),
            F.col('service'),
        )
        .agg(
            F.count(F.lit(1)).alias('total'),
            F.sum('is_error').alias('errors'),
            F.avg('status').alias('avg_status'),
        )
        .withColumn('error_rate', (F.col('errors') / F.col('total')).cast('double')) # windowed error rate
        .select(
            F.col('window.start').alias('window_start'),
            F.col('window.end').alias('window_end'),
            'service',
            'total',
            'errors',
            'error_rate',
            'avg_status',
        )
        .orderBy(F.col('window_start').asc(), F.col('service').asc())
    )

    return windowed
