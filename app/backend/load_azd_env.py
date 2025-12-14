import json
import logging
import os
import subprocess

from dotenv import load_dotenv

logger = logging.getLogger("scripts")


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv"""
    result = subprocess.run("azd env list -o json", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        # If azd is not installed, try to find .env file manually
        logger.warning("azd command not found, attempting to load .env from .azure directory")
        for env_dir in [".azure/cpr-rag", ".azure"]:
            env_path = os.path.join(os.getcwd(), env_dir, ".env")
            if os.path.exists(env_path):
                logger.info(f"Loading environment from {env_path}")
                loading_mode = os.getenv("LOADING_MODE_FOR_AZD_ENV_VARS") or "override"
                if loading_mode == "no-override":
                    load_dotenv(env_path, override=False)
                else:
                    load_dotenv(env_path, override=True)
                return
        logger.warning("No .env file found, continuing without azd environment")
        return
    env_json = json.loads(result.stdout)
    env_file_path = None
    for entry in env_json:
        if entry["IsDefault"]:
            env_file_path = entry["DotEnvPath"]
    if not env_file_path:
        raise Exception("No default azd env file found")
    loading_mode = os.getenv("LOADING_MODE_FOR_AZD_ENV_VARS") or "override"
    if loading_mode == "no-override":
        logger.info("Loading azd env from %s, but not overriding existing environment variables", env_file_path)
        load_dotenv(env_file_path, override=False)
    else:
        logger.info("Loading azd env from %s, which may override existing environment variables", env_file_path)
        load_dotenv(env_file_path, override=True)
