import re
from telegram_client import TelegramClient
from rail_client import RailClient

telegram_client = TelegramClient()
rail_client = RailClient()


def generate_response(text):
    m = re.search(r"([A-Z]{3}) TO ([A-Z]{3})", text.upper())

    if not m:
        response = (
            "Unrecognised format for departures query. "
            "Expected format: [CRS] to [CRS]"
        )
    else:
        origin, destination = m.group(1), m.group(2)
        rail_client.fetch_services_for_trip(origin, destination)
        response = rail_client.get_services_text()

    return response


def response_loop():
    try:
        while True:
            telegram_client.fetch_updates()
            message = telegram_client.get_last_human_message()
            if not message:
                continue
            else:
                response = generate_response(message["text"])
                telegram_client.send_message(message["chat_id"], response)

    except KeyboardInterrupt:
        print("Program terminated by user.")
