# src/config/config.py

import os
import yaml
from utils.logger import get_logger

logger = get_logger()


def load_config(mode="dev"):
    """Load configuration from YAML file and environment variables."""
    # Try mode-specific config first
    config_path = f"src/config/config.{mode}.yaml"
    
    # If mode-specific config doesn't exist, fall back to base config
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found, falling back to base config.yaml")
        config_path = "src/config/config.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    config["bq"]["source_table"] = os.getenv(
        "BQ_SOURCE_TABLE", config["bq"]["source_table"]
    )
    config["bq"]["output_table"] = os.getenv(
        "BQ_OUTPUT_TABLE", config["bq"]["output_table"]
    )
    
    config["models"]["model_version"] = os.getenv(
        "MODEL_VERSION", config["models"].get("model_version", "v0.1")
    )
    config["models"]["embedding_model"] = os.getenv(
        "EMBEDDING_MODEL", config["models"]["embedding_model"]
    )
    
    config["runtime"]["partition_date"] = os.getenv(
        "PARTITION_DATE", config["runtime"]["partition_date"]
    )
    
    return config