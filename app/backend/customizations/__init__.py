# Backend customizations package

from .config import is_feature_enabled, get_deployment_metadata

__all__ = [
    "is_feature_enabled",
    "get_deployment_metadata",
]
