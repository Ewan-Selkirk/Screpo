import json
from os.path import expanduser, exists

import mss
from PIL import Image
from PySide6.QtGui import QGuiApplication


VERSION = "0.0.5"
BUILD = "Dev"


class Utils:
    def __init__(self, app: QGuiApplication = ...):
        self.version = VERSION
        self.build = BUILD

        self.app_ref = app
        self.clipboard = app.clipboard()
        self.history = {}

        self.settings = Settings()

        with mss.mss() as mons:
            self.monitors = mons.monitors[1:]

    def capture_monitors(self) -> list[Image]:
        shots = []

        with mss.mss() as sct:
            for mon in self.monitors:
                shot = sct.grab(mon)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                shots.append(img)

        if len(self.history) > self.settings.values["general"]["performance"]["history_max_items"]:
            del self.history[list(self.history.keys())[0]]

        if len(self.history):
            self.history[list(self.history.keys())[-1] + 1] = shots
        else:
            self.history[0] = shots
        return shots


class Settings:
    def __init__(self):
        self.values: dict = ...

        if not self.load():
            self.create()
        else:
            self.check()

    @staticmethod
    def get_default_settings() -> dict:
        return {
            "general": {
                "features": {
                    "enable_opencv": False
                },
                "performance": {
                    "history_max_items": 8
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
        if exists(expanduser("~") + r"/.screpo"):
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

    def check(self):
        # This will cause issues say if a setting is removed while another is added
        # TODO: Switch from using the length as the condition
        if nested_dict_len(self.values) < nested_dict_len(self.get_default_settings()):
            self.values.update({k: v for k, v in self.get_default_settings().items() if k not in self.values.keys()})

            for k, v in self.get_default_settings().items():
                self.values[k].update({nk: nv for nk, nv in self.get_default_settings()[k].items()
                                       if nk not in self.values[k].keys()})
                for k2, v2 in self.get_default_settings()[k].items():
                    self.values[k][k2].update({nk: nv for nk, nv in self.get_default_settings()[k][k2].items()
                                               if nk not in self.values[k][k2].keys()})

            self.save()
            print("Settings: Successfully mitigated new settings over to old save file")


# Stolen from Example 2 on GeeksForGeeks
# https://www.geeksforgeeks.org/get-length-of-dictionary-in-python/
def nested_dict_len(d):
    length = len(d)
    for key, value in d.items():
        if isinstance(value, dict):
            length += nested_dict_len(value)
    return length

