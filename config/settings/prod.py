"""
Prod - настройки для продуктивного запуска
"""
from dotenv import load_dotenv
from pathlib import Path

ENV_DEV_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ENV_DEV_DIR / '.env.prod')

from .base import *

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = False