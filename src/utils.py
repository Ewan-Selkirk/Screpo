import mss
from PIL import Image


def capture_monitors() -> list[Image]:
    shots = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            shots.append(img)

    return shots
