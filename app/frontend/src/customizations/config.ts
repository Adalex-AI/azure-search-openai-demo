// Custom Features Configuration
// ==============================
// Enable/disable custom features here without modifying upstream code.
// This file is the single source of truth for frontend feature flags.

export const CUSTOM_FEATURES = {
    // Category filtering feature - adds category dropdown in chat/ask pages
    categoryFilter: true,

    // Citation sanitization - fixes malformed citations like "1. 1" -> "[1]"
    citationSanitizer: true,

    // Legal domain customizations (prompts are handled backend-side)
    legalDomainPrompts: true
};

export function isFeatureEnabled(featureName: keyof typeof CUSTOM_FEATURES): boolean {
    return CUSTOM_FEATURES[featureName] ?? false;
}
