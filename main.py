import os
import sys
from dotenv import load_dotenv

# PyInstaller: данные в sys._MEIPASS; иначе — рядом с main.py
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(__file__)

load_dotenv(os.path.join(_base, ".env"))

from ui.app import main

if __name__ == "__main__":
    main()
