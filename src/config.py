import logging
from dotenv import load_dotenv
import os

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
NYT_API_KEY = os.getenv("NYT_API_KEY", "")
LOGGING_LEVEL = logging.DEBUG
