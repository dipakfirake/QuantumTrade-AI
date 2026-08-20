"""
Secrets loader helper.

Reads API keys from environment variables or a .env file (if python-dotenv
is installed). Do NOT commit secret values to source control.
"""
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; environment variables still work
    pass


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val
