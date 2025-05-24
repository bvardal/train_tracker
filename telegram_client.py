import re
import requests
from config import TELEGRAM_TOKEN
from rail_client import RailClient


class TelegramClient:
    def __init__(self):
        self.last_update_id = 0
        self.last_updates = []
        self.base_url = "https://api.telegram.org/bot"
        self.base_url += TELEGRAM_TOKEN

        self.endpoints = {
            "updates": self.base_url + "/getUpdates"
        }

    def fetch_updates(self):
        response = requests.get(
            self.base_url + "/getUpdates",
            {"timeout": 30, "offset": self.last_update_id}
        )
        response.raise_for_status()
        self.last_updates = response.json().get("result", [])

    def get_last_message(self):
        if not self.last_updates:
            return None
        else:
            last_result = self.last_updates[-1]

        self.last_update_id = last_result["update_id"] + 1
        message = last_result["message"]

        if not message["from"]["is_bot"]:
            return {
                "chat_id": message["chat"]["id"],
                "text": message["text"]
            }
        else:
            return None

    def send_message(self, payload):
        response = requests.post(self.base_url + "/sendMessage", data=payload)
        response.raise_for_status()
        return response

    def respond_to_request(self):
        message = self.get_last_message()

        if not message:
            return

        text = message["text"].upper()
        m = re.search(r"([A-Z]{3}) TO ([A-Z]{3})", text)
        if not m:
            message["text"] = "Unrecognised format"
            return self.send_message(message)

        origin, destination = m.group(1), m.group(2)
        client = RailClient()

        message["text"] = client.get_departures(origin, destination)
        return self.send_message(message)
