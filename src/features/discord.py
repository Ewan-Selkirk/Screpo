from io import BytesIO

import requests
from PIL import Image

from src.utils import Utils


class Discord:
    def __init__(self, utils: Utils):
        self.username = utils.settings.values["discord"]["username"]
        self.webhook = utils.settings.values["discord"]["webhook_url"]

        self.data = {
            "username": self.username
        }

    def send_to_webhook(self, image: Image):
        with BytesIO() as binary:
            image.save(binary, 'PNG')
            binary.seek(0)
            requests.post(self.webhook, data=self.data, files={f"Screpo Screenshot.png": binary})

        print("Discord: Image sent to webhook")

    def send_to_webhook_with_message(self, image: Image, message: str):
        self.data["content"] = message

        self.send_to_webhook(image)


class Webhook:
    def __init__(self, name: str, webhook: str, username: str):
        self.__name = name
        self.__webhook = webhook
        self.__username = username

    def get_webhook(self) -> str:
        return self.__webhook

    def get_username(self) -> str:
        return self.__username
