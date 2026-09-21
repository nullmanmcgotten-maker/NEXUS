from __future__ import annotations

from nexus_engine.config import load_settings
from nexus_engine.order_lifecycle import LiveOrderLifecycle


def main() -> None:
    lifecycle = LiveOrderLifecycle(load_settings())
    result = lifecycle.validate_account()
    print(result)


if __name__ == "__main__":
    main()
