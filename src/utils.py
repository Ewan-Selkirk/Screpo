import os.path
import json
from os.path import expanduser

import mss
from PIL import Image


class Settings:
    def __init__(self):
        self.values = ...

        if not self.load():
            self.create()

    @staticmethod
    def get_default_settings() -> dict:
        return {
            "general": {
                "features": {
                    "enable_opencv": False
                }
            },
            "opencv": {

            }
        }

    def create(self):
        self.values = self.get_default_settings()
        print("Settings: No settings file found. Creating a new one")
        self.save()

    def load(self) -> bool:
        if os.path.exists(expanduser("~") + r"/.screpo"):
            try:
                with open(expanduser("~") + r"/.screpo", "r") as f:
                    self.values = json.load(f)
                    print("Settings: Settings file found and loaded")
                    return True
            except IOError:
                print("Settings: Settings file corrupt or unreadable. Creating a new one")
                self.create()
        else:
            return False

    def save(self, data: dict = ...):
        if data is Ellipsis:
            data = self.values

        with open(expanduser("~") + r"/.screpo", "w") as f:
            json.dump(data, f)

        print(f"Settings: Saved data to {expanduser('~') + r'/.screpo'}")


def capture_monitors() -> list[Image]:
    shots = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            shots.append(img)

    return shots
