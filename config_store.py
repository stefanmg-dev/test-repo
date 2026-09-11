import json
from pathlib import Path

CONFIG_PATH = Path("document_types.json")

def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg: dict):
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)
