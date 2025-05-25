import requests
from config import TELEGRAM_TOKEN


class TelegramClient:
    def __init__(self):
        self.last_update_id = 0
        self.last_updates = []
        self.base_url = "https://api.telegram.org/bot"
        self.base_url += TELEGRAM_TOKEN

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
                "user_id": message["from"]["id"],
                "chat_id": message["chat"]["id"],
                "text": message["text"]
            }
        else:
            return None

    def send_message(self, chat_id, text):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        response = requests.post(self.base_url + "/sendMessage", data=payload)
        response.raise_for_status()
        return response
