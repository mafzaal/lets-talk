"""Scheduler configuration utilities."""
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def create_default_scheduler_config() -> Dict[str, Any]:
    """Create a default scheduler configuration."""
    return {
        "scheduler_type": "background",
        "max_workers": 4,
        "executor_type": "thread",
        "enable_persistence": True,
        "jobs": [
            {
                "id": "daily_blog_update",
                "name": "Daily Blog Update",
                "type": "cron",
                "hour": 2,
                "minute": 0,
                "config": {
                    "force_recreate": False,
                    "ci_mode": True,
                    "use_chunking": True,
                    "should_save_stats": True
                }
            }
        ]
    }


def save_scheduler_config_to_file(config: Dict[str, Any], filename: str) -> None:
    """Save scheduler configuration to a JSON file."""
    try:
        config_path = Path(filename)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Scheduler configuration saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save scheduler configuration to {filename}: {e}")
        raise


def load_scheduler_config_from_file(filename: str) -> Dict[str, Any]:
    """Load scheduler configuration from a JSON file."""
    try:
        config_path = Path(filename)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file {filename} not found")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Scheduler configuration loaded from {filename}")
        return config
    except Exception as e:
        logger.error(f"Failed to load scheduler configuration from {filename}: {e}")
        raise
