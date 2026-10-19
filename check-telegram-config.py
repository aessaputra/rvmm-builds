#!/usr/bin/env python3
"""Run with python3 check-telegram-config.py; uses dummy values only."""
from copy import deepcopy
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("prepare", Path(__file__).with_name("prepare-telegram-config.py"))
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = {"Telegram": {"included-patches": f'"{module.PATCH}"', "patcher-args": "-Oexisting=true"}, "Other": {}}
env = {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "a" * 32}
result = module.prepare(deepcopy(config), env)
assert result["Telegram"]["patcher-args"] == "-Oexisting=true -OapiId=12345 -OapiHash=" + "a" * 32
assert result["Other"] == {}
assert module.prepare({"Other": {}}, {}) == {"Other": {}}
assert module.prepare({"Telegram": {"enabled": False}}, {}) == {"Telegram": {"enabled": False}}
for bad in [{}, {**env, "TELEGRAM_API_ID": "2147483648"}, {**env, "TELEGRAM_API_ID": "1;exit"}, {**env, "TELEGRAM_API_HASH": "invalid"}]:
    try:
        module.prepare(deepcopy(config), bad)
    except ValueError as error:
        assert "a" * 32 not in str(error)
    else:
        raise AssertionError("Invalid credentials accepted")
print("Telegram config checks passed")
