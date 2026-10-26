
import json
import os
import time

import pika


RABBITMQ_HOST = "localhost"
QUEUE_NAME = "events"
CONSUMER_ID = os.getenv("CONSUMER_ID", "consumer-1")
PROCESSING_DELAY = 2


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    def process_message(ch, method, properties, body):
        message = body.decode("utf-8")

        print(f"\n[{CONSUMER_ID}] Received: {message}", flush=True)

        # Simulate work being performed.
        time.sleep(PROCESSING_DELAY)

        print(f"[{CONSUMER_ID}] Finished processing", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=process_message,
        auto_ack=False,
    )

    print(
        f"[{CONSUMER_ID}] Waiting for messages on '{QUEUE_NAME}'...",
        flush=True,
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n[{CONSUMER_ID}] Stopping...", flush=True)
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
