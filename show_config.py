from __future__ import annotations

from nexus_engine.config import load_settings


if __name__ == "__main__":
    settings = load_settings()
    print(settings)
