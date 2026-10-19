#!/usr/bin/env python3
"""Inject Telegram credentials into the runner-only JSON configuration."""
import json
import os
from pathlib import Path
import re
import sys

PATCH = "Use registered Telegram API credentials"


def prepare(config, env):
    telegram = config.get("Telegram", {})
    if not telegram.get("enabled", True) or PATCH not in telegram.get("included-patches", ""):
        return config
    api_id = env.get("TELEGRAM_API_ID", "").strip()
    api_hash = env.get("TELEGRAM_API_HASH", "").strip()
    if not re.fullmatch(r"[1-9][0-9]*", api_id) or len(api_id) > 10 or int(api_id) > 2147483647:
        raise ValueError("TELEGRAM_API_ID must be a positive 32-bit integer")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", api_hash):
        raise ValueError("TELEGRAM_API_HASH must contain 32 hexadecimal characters")
    telegram["patcher-args"] = (telegram.get("patcher-args", "") +
                               f" -OapiId={api_id} -OapiHash={api_hash}").strip()
    return config


if __name__ == "__main__":
    try:
        config = prepare(json.load(sys.stdin), os.environ)
        output = Path("config.json")
        output.touch(mode=0o600, exist_ok=True)
        output.chmod(0o600)
        output.write_text(json.dumps(config))
    except (ValueError, OSError) as error:
        sys.exit(str(error))
