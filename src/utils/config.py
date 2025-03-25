"""
Configuration utilities for the OCI MCP Server
"""
import logging
import os
from typing import Any, Dict

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
    """
    logger = logging.getLogger(__name__)
    
    try:
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        # Return default configuration
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "log_level": "info"
            },
            "security": {
                "cors_origins": ["*"]
            }
        }


def get_oci_config() -> Dict[str, Any]:
    """
    Get OCI configuration from the loaded config
    
    Returns:
        Dictionary containing OCI configuration
    """
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if not os.path.exists(config_path):
        config_path = "config.example.yaml"
    
    config = load_config(config_path)
    return config.get("oci", {})
