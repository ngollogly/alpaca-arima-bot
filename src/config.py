from dataclasses import dataclass
import os
from dotenv import load_dotenv
from pathlib import Path

# Always load .env from the project root (the folder that contains /src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")  # <— force-load .env

@dataclass
class Settings:
    api_key: str = os.getenv("ALPACA_API_KEY_ID", "")
    api_secret: str = os.getenv("ALPACA_API_SECRET_KEY", "")
    env: str = os.getenv("ALPACA_ENV", "paper").lower()
    log_dir: str = os.getenv("LOG_DIR", "logs")
    data_dir: str = os.getenv("DATA_DIR", "data")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    default_notional: float = float(os.getenv("DEFAULT_NOTIONAL", "1.00"))

settings = Settings()
