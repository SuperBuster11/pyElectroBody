"""
Convert original Electro Body sounds (*.u8: raw unsigned 8-bit mono, 8000 Hz)
to 16-bit WAV files.

Usage: python convert_sounds.py [source_folder] [destination_folder]
Defaults: olddata -> newdata (next to this script).
"""

import os
import sys
import glob
import wave
import array

HERE = os.path.dirname(os.path.abspath(__file__))
RATE = 8000


def convert(source, target):
    with open(source, "rb") as f:
        raw = f.read()
    samples = array.array("h", ((b - 128) * 256 for b in raw))
    if sys.byteorder == "big":
        samples.byteswap()
    with wave.open(target, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "olddata")
    destination = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "newdata")
    os.makedirs(destination, exist_ok=True)
    for filename in sorted(glob.glob(os.path.join(folder, "*.u8"))):
        name = os.path.splitext(os.path.basename(filename))[0]
        convert(filename, os.path.join(destination, name + ".wav"))
        print("Converted:", name)
    print("Done.")


if __name__ == '__main__':
    main()
