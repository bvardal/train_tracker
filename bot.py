import re
from telegram_client import TelegramClient
from rail_client import RailClient

telegram_client = TelegramClient()
rail_client = RailClient


def generate_response(message):
    text = message["text"].upper()
    m = re.search(r"([A-Z]{3}) TO ([A-Z]{3})", text)

    if not m:
        message["text"] = (
            "Unrecognised format for departures query. "
            "Expected format: [CRS] to [CRS]"
        )
    else:
        origin, destination = m.group(1), m.group(2)
        client = RailClient()

        message["text"] = client.get_departures(origin, destination)

    return message


def response_loop():
    try:
        while True:
            telegram_client.fetch_updates()
            message = telegram_client.get_last_human_message()
            if not message:
                continue
            else:
                response = generate_response(message)
                telegram_client.send_message(response)

    except KeyboardInterrupt:
        print("Program terminated by user.")
