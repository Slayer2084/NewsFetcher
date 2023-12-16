import logging
from dotenv import load_dotenv
import os

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
NYT_API_KEY = os.getenv("NYT_API_KEY", "")
LOGGING_LEVEL = logging.DEBUG
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
DB_USER = os.getenv("DB_USER", "")
DB_HOST = os.getenv("DB_HOST", "")
DB_PASS = os.getenv("DB_PASS", "")
DB_PORT = os.getenv("DB_PORT", "")
DB_NAME = os.getenv("DB_NAME", "")
