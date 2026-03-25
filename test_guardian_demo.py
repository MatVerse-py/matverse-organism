#!/usr/bin/env python3
"""Small smoke test for Guardian modules."""

from guardian_config import preset_balanced


def main() -> int:
    cfg = preset_balanced()
    print("Guardian preset loaded:", cfg.base_url, cfg.check_interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
