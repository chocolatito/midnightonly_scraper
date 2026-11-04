from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(".env")
BASE_DIR = str(Path(__file__).parents[1])
LOG_NAME = f"{Path(__file__).parents[1].parts[-1]}.log"
FILE_DIR = "FILES"
HEADERS = {'accept-language': 'en;q=0.9'}
PROXY = os.getenv("PROXY", None)
