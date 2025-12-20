import json
import logging
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("scripts")


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv.
    
    Falls back to a local .env file if no azd environment is configured.
    """
    # First, try to load from azd environment
    result = subprocess.run("azd env list -o json", shell=True, capture_output=True, text=True)
    env_file_path = None
    
    if result.returncode == 0 and result.stdout.strip():
        try:
            env_json = json.loads(result.stdout)
            for entry in env_json:
                if entry.get("IsDefault"):
                    env_file_path = entry.get("DotEnvPath")
                    break
        except json.JSONDecodeError:
            pass
    
    # Fallback: check for local .env file in backend directory
    if not env_file_path:
        local_env = Path(__file__).parent / ".env"
        if local_env.exists():
            env_file_path = str(local_env)
            logger.info("No azd env found, using local .env file: %s", env_file_path)
        else:
            raise Exception(
                "No default azd env file found and no local .env file exists. "
                "Either run 'azd up' to create an Azure environment, "
                "or copy .env.sample to .env and configure your Azure services."
            )
    
    loading_mode = os.getenv("LOADING_MODE_FOR_AZD_ENV_VARS") or "override"
    if loading_mode == "no-override":
        logger.info("Loading azd env from %s, but not overriding existing environment variables", env_file_path)
        load_dotenv(env_file_path, override=False)
    else:
        logger.info("Loading azd env from %s, which may override existing environment variables", env_file_path)
        load_dotenv(env_file_path, override=True)
