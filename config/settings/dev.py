"""
Dev - настройк для локальной разработке
"""
from dotenv import load_dotenv
from pathlib import Path

ENV_DEV_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ENV_DEV_DIR / '.env.dev')

from .base import *

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]