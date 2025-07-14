# config/config.py

import os
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(mode="dev"):
    base_path = os.path.dirname(__file__)
    config_path = os.path.join(base_path, "config.yaml")
    
    # Load base config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    config["bq"]["source_table"] = os.getenv("BQ_SOURCE_TABLE", config["bq"]["source_table"])
    config["bq"]["output_table"] = os.getenv("BQ_OUTPUT_TABLE", config["bq"]["output_table"])
    
    config["models"]["model_version"] = os.getenv("MODEL_VERSION", config["models"].get("model_version", "v0.1"))
    config["models"]["embedding_model"] = os.getenv("EMBEDDING_MODEL", config["models"]["embedding_model"])
    
    config["runtime"]["mode"] = mode
    # Default to false for wet runs, only true if explicitly set
    dry_run_env = os.getenv("DRY_RUN", "false")
    config["runtime"]["dry_run"] = dry_run_env.lower() == "true"
    config["runtime"]["partition_date"] = os.getenv("PARTITION_DATE", config["runtime"]["partition_date"])
    
    return config