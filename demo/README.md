# Steraming Data Analysis

## Introduction

You are working on a system that aggregates logs from multiple microservices. For each log is registered as an event containing the following information:

* The service name
* The timestamp when it occurred
* An *almost* arbitrary message about what happened.

In principle, the message can be arbitrary, the developer picks the message they want to log at anytime to help them debug. However, logging the status code of the response of any microservice is standarized so that they all look like HTTP Status Code: XXX. This way you can easily compare different services and see which one has more errors.

The data source for the task is going to be a directory in which JSON files are stored. Each JSON file looks like:

```json
{"service": "monitoring", "timestamp": 1745319168.057018, "message": "HTTP Status Code: 200"}
```

## Task 1: Running Averages

This is the simplest way to compute statistics overan ever growing dataset. You need to figure out a way to compute statistics about your data by delaying the execution of formulas that require information about a dataset. Recall that the formular for computing an average is:

$$
\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
$$

Where $n$ is the number of elements in the dataset and $x_i$ is the $i$-th element in the dataset. Now, you could keep two counters, one for the number of elements and one for the sum of the elements. Then, you could compute the average by dividing the sum by the number of elements at that point in time, the formula would be like:

$$
\bar{x}_t = \frac{1}{n_t} \sum_{i=1}^{n_t} x_i
$$

It is important to highlight that you compute statistics up to a point with this method.

For this task you need to implement an algorithm that allows you to compute the average number of successful requests per service.


## Task 2: Sliding Windows

There are some statistics that are relevant over a certain period of time. For example, you might want to compute the average number of unsuccessful requests over the last 10 minutes. To do this, you can use a sliding window: keep track of records over a fixed period of time and compute the statistics over those records that you allow yourself to keep in memory.

Implement an sliding window algorithm that allows you to compute the average number of unsuccessful requests over the last minute.


## Task 3: Sampling

There are situations in which we need to take samples of the data to be able to compute any statistic. However, when working with streaming data, you need to keep into account that the full set of elements for which you want to compute statistics is not available. Let's say you want need a sample and you want to make sure that the sample is representative of the full dataset; how do you ensure that the samples are chosen in a truly random way?

Your task now is to implement the Reservoir Sampling algorithm to figure out *the most commong HTTP Status Code in the dataset*. Here is another reference: https://medium.com/pythoneers/dipping-into-data-streams-the-magic-of-reservoir-sampling-762f41b78781


## Task 4: Filtering

Our system is connected to a lot of services, all of them generating a lot of logs. However, there are some type of messages in the logs, for which we are specially interested. Those messages for which we are interested, should be sent to another system (e.g. a database).

Let's say we have a list of messages that we are interested in and they are stored in a file, but the file is too big to fit in memmory. Use the [Bloom Filter](https://en.wikipedia.org/wiki/Bloom_filter) technique to decide whether those messages should be forwarded to antoher system or not.

## Task 5: Polars Streaming

Polars can handle streaming data by using the LazyFrame interface. Read its documentation and propose some statistics that you can compute with its API. Feel free to decide which set of statistics are interesting to compute with this approach and explain why you chose those. References:

* https://docs.pola.rs/user-guide/concepts/streaming/ 
* https://urbandataengineer.substack.com/p/big-data-small-machine-the-magic/
* https://www.rhosignal.com/posts/streaming-in-polars/
* https://www.rhosignal.com/posts/streaming-operations-in-polars/ 

## Task 6: Spark Streaming

Spark can handle streaming data by using the Structured Streaming API. Read its documentation and propose some statistics that you can compute with its API. Feel free to decide which set of statistics are interesting to compute with this approach and explain why you chose those. References:
* https://spark.apache.org/docs/latest/streaming-programming-guide.html
* https://spark.apache.org/docs/latest/streaming/getting-started.html 
