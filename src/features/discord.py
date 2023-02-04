from io import BytesIO
from datetime import datetime

import requests
from PySide6.QtWidgets import QInputDialog, QLineEdit

from utils import Utils


class Webhook:
    def __init__(self, name: str, url: str, username: str):
        self.name = name
        self.url = url
        self.username = username


class Discord:
    def __init__(self, utils: Utils):
        self.utils = utils

        self.username = utils.settings.values["discord"]["username"]
        self.webhooks = utils.settings.values["discord"]["webhooks"]

        self.data = {}

    def send_to_webhook(self, webhook: Webhook, image):
        if webhook.username != "":
            self.data["username"] = webhook.username
        elif self.utils.settings.values["discord"]["username"] is not None:
            self.data["username"] = self.utils.settings.values["discord"]["username"]

        if callable(image):
            image = image()

        with BytesIO() as binary:
            image.save(binary, 'PNG')
            binary.seek(0)
            req = requests.post(
                webhook.url,
                data=self.data,
                files={f"{''.join([c for c in str(datetime.now()) if c.isalnum()])}-screpo.png": binary}
            )

            if req.status_code == 200:
                print(f"Discord: Image sent to webhook: {webhook.name}")
            else:
                print(f"Discord: Failed to send to the webhook ({req.content}: {req.status_code})")

    def send_to_webhook_with_message(self, parent, webhook: Webhook, image):
        message, boolean = QInputDialog().getMultiLineText(parent, "Send Image to Webhook with Message", "Message:")

        if boolean:
            self.data["content"] = message
            self.send_to_webhook(webhook, image)

        # As the reference to the Discord class is persistent
        # we need to delete the content or all following images will have
        # the same content
        del self.data["content"]
