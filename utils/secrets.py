"""
Secrets loader helper.

Reads API keys from environment variables or a .env file.
"""
import os
from typing import Optional

def _load_env_file():
    """Load key-value pairs from .env file into os.environ if present."""
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass
    
    # Built-in fallback parser
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    _load_env_file()
    return os.environ.get(key, default)

def require_env(key: str) -> str:
    val = get_env(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val
