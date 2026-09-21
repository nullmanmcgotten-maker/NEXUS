from __future__ import annotations

from nexus_engine.config import load_settings
from nexus_engine.engine_loop import EngineLoop


def main() -> None:
    settings = load_settings()
    loop = EngineLoop(settings)
    result = loop.run_once()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    import json
    main()
