import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from ui.app import main

if __name__ == "__main__":
    main()
