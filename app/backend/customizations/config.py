# Custom features configuration
# Enable/disable custom features here without modifying upstream code

CUSTOM_FEATURES = {
    # Category filtering feature - adds /api/categories endpoint and UI dropdown
    "category_filter": True,
    
    # Custom citation formatting in prompts
    "legal_domain_prompts": True,
    
    # Frontend citation sanitization
    "citation_sanitizer": True,
    
    # Custom evaluation scripts
    "custom_evals": True,
}


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a custom feature is enabled."""
    return CUSTOM_FEATURES.get(feature_name, False)
