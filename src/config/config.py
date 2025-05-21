# config/config.py

import os
import yaml

def load_config(mode="dev"):
    base_path = os.path.dirname(__file__)
    config_path = os.path.join(base_path, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config["runtime"]["mode"] = mode
    return config