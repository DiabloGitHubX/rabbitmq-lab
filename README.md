# RabbitMQ Messaging Lab

A Python-based messaging system using RabbitMQ and Docker Compose. This project demonstrates asynchronous communication, message persistence, producer-consumer workflows, HTTP API publishing, acknowledgments, and competing consumers.

## Project Overview

The project contains a Python producer that publishes 10 user activity events to a RabbitMQ queue and a Python consumer that processes messages from that queue.

RabbitMQ acts as a message broker between the producer and consumer. Messages can remain queued when no consumer is running and can be processed later when a consumer becomes available.

### Technologies

- Python 3.14
- RabbitMQ 3 Management
- Docker and Docker Compose
- Pika 1.3.2
- RabbitMQ HTTP Management API
- Git and GitHub

## Architecture

```text
                  Python Producer
                         |
                         | AMQP (Pika)
                         v
                +------------------+
                |     RabbitMQ     |
                |                  |
                |  Queue: events   |
                +------------------+
                         |
                  +------+------+ 
                  |      |      |
                  v      v      v
               Consumer 1  Consumer 2  Consumer 3

        Alternative publishing method:
             curl -> HTTP Management API
                         |
                         v
                  RabbitMQ Queue
```

The producer generates JSON events containing:

- `username` — the user associated with the event.
- `event_type` — the activity, such as login, logout, page view, or purchase.
- `timestamp` — the event creation time in UTC.

## Project Structure

```text
rabbitmq-lab/
├── app/
│   ├── producer.py
│   └── consumer.py
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
└── screenshots/
```

The screenshots/ directory contains evidence captured during testing, including queue state before and after processing, producer output, and competing-consumer behavior.

## Prerequisites

Install the following software:

- Docker Desktop with the Linux container engine running
- Python 3
- Git
- A web browser

## Setup

### 1. Start RabbitMQ

From the project root, run:

```bash
docker compose up -d
```

Verify that the container is running:

```bash
docker compose ps
```

RabbitMQ exposes these ports:

| Port | Purpose |
|---|---|
| `5672` | AMQP messaging protocol |
| `15672` | Management dashboard and HTTP API |

### 2. Open the management dashboard

Navigate to:

http://localhost:15672

For this local development configuration, the default credentials are:

- Username: `guest`
- Password: `guest`

These default credentials are for local testing only and should not be used as production credentials.

### 3. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

The required Python dependency is Pika, the RabbitMQ client library.

## Running the Producer

Run:

```bash
python app/producer.py
```

The producer creates the durable `events` queue if it does not exist and publishes 10 JSON messages.

Each message is published through RabbitMQ's default exchange using the routing key `events`. Messages are marked persistent using delivery mode 2.

Expected final output:

```text
Producer finished. Sent 10 messages.
```

## Running the Consumer

Run:

```bash
python app/consumer.py
```

The consumer subscribes to the `events` queue, decodes incoming UTF-8 messages, and prints their contents.

The consumer uses manual acknowledgments. Each message is acknowledged after the simulated processing delay.

### Consumer configuration

- `CONSUMER_ID` identifies the consumer instance.
- `PROCESSING_DELAY` simulates two seconds of processing time.
- `prefetch_count=1` limits each consumer to one unacknowledged message at a time.
- `auto_ack=False` enables explicit acknowledgments.

## Testing and Observations

### Test 1: Producer without a consumer

The producer was run while no consumer was listening.

Observed result:

| Metric | Value |
|---|---:|
| Messages published | 10 |
| Ready | 10 |
| Unacked | 0 |
| Total | 10 |

This demonstrated that RabbitMQ can buffer messages until a consumer becomes available.

### Test 2: Start the consumer

The consumer was started after the 10 messages had accumulated in the queue.

All 10 JSON events were received and printed. After successful processing and acknowledgments, the queue was empty.

### Test 3: Publish using the HTTP Management API

A plain-text message was published using `curl`:

```bash
curl -u guest:guest \
  -H "content-type: application/json" \
  -X POST \
  http://localhost:15672/api/exchanges/%2F/amq.default/publish \
  -d "{\"properties\":{},\"routing_key\":\"events\",\"payload\":\"Message sent via curl\",\"payload_encoding\":\"string\"}"
```

RabbitMQ returned:

```json
{"routed":true}
```

This confirmed that the message was routed successfully to the queue.

The consumer was subsequently updated to handle both JSON and plain-text messages.

### Test 4: Competing consumers — bonus challenge

Three consumer instances were started simultaneously, each with a different `CONSUMER_ID`.

The producer published 10 messages, and the consumers processed them with a simulated two-second delay.

Observed distribution:

| Consumer | Messages processed |
|---|---:|
| Consumer 1 | 3 |
| Consumer 2 | 3 |
| Consumer 3 | 4 |
| **Total** | **10** |

This demonstrated how multiple consumers can share work from a single queue. The distribution is not guaranteed to be equal in every run because it depends on timing and consumer availability.

### Final queue state

After processing was completed, the RabbitMQ dashboard showed:

| Metric | Final value |
|---|---:|
| Ready | 0 |
| Unacked | 0 |
| Total | 0 |

## Key Concepts

### What is a message broker?

A message broker receives messages from producers and routes them to queues or consumers. RabbitMQ separates the producer from the consumer, allowing them to operate independently.

### What is asynchronous communication?

The producer can publish a message without waiting for the consumer to process it. RabbitMQ stores the message until it can be delivered, decoupling the timing of the two applications.

### What happens when no consumer is running?

Messages remain in the queue until they are consumed, rejected, expired, or otherwise removed. In this lab, the 10 messages remained Ready until the consumer started.

### Why use a queue instead of direct HTTP requests?

A queue provides buffering and decouples the sender from the receiver. It helps handle traffic spikes and allows consumers to process work independently. Direct HTTP requests are useful when an immediate response is needed, but the caller and receiver are more tightly coupled in time.

### What happens when multiple consumers listen to one queue?

RabbitMQ distributes messages among competing consumers. Each message is delivered to one consumer, not broadcast to all of them.

### How can consumers help scale a system?

Additional consumer instances can process queued work concurrently. This increases processing capacity when the workload can be handled independently. Actual throughput depends on processing time, available resources, and application behavior.

### What is the difference between Ready and Unacked?

- **Ready:** messages waiting to be delivered.
- **Unacked:** messages delivered to consumers that have not yet been acknowledged.
- **Total:** the combined Ready and Unacked message count.

### Why use acknowledgments?

Acknowledgments tell RabbitMQ that a consumer has finished processing a message. Manual acknowledgments allow RabbitMQ to track in-flight messages and redeliver unacknowledged messages if a consumer connection fails.

### What does prefetch count do?

A prefetch count limits the number of unacknowledged messages RabbitMQ can deliver to a consumer at a time. A value of 1 helps distribute work among consumers that process messages at different speeds.

### What is the difference between RabbitMQ and HTTP?

HTTP is a request-response protocol commonly used for synchronous API communication. RabbitMQ is a message broker that supports asynchronous delivery and buffering. RabbitMQ's Management API itself uses HTTP, while this project's Python producer uses AMQP through Pika.

## Limitations and Future Improvements

Possible improvements include:

- Add automated tests for producer and consumer behavior.
- Add structured logging and configuration through environment variables.
- Add retry policies and a dead-letter queue for failed messages.
- Add health checks and more restrictive production credentials.
- Containerize the Python applications for a fully containerized deployment.
- Add monitoring and metrics for message throughput and consumer performance.

## Cleanup

To stop and remove the RabbitMQ container and project network, run:

```bash
docker compose down
```

The named RabbitMQ data volume is preserved by this command. To remove the volume as well, use `docker compose down -v` only when the stored data is no longer needed.

## Conclusion

This project demonstrates RabbitMQ-based asynchronous messaging with Python, message persistence, manual acknowledgments, HTTP API publishing, queue monitoring, and competing consumers. The three-consumer experiment showed how a shared queue can distribute work across multiple workers.
