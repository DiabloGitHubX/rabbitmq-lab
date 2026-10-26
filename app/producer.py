
import json
import random
from datetime import datetime, timezone

import pika


RABBITMQ_HOST = "localhost"
QUEUE_NAME = "events"


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Create the queue if it does not already exist.
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    usernames = ["alice", "bob", "charlie", "diana"]
    event_types = ["login", "logout", "page_view", "purchase"]

    for i in range(10):
        event = {
            "username": random.choice(usernames),
            "event_type": random.choice(event_types),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        message = json.dumps(event)

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )

        print(f"Sent message {i + 1}/10: {message}")

    connection.close()
    print("Producer finished. Sent 10 messages.")


if __name__ == "__main__":
    main()
