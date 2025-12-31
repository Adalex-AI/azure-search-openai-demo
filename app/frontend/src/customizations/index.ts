// Frontend Customizations Module
// ===============================
// This module contains custom features that are isolated from the main codebase
// to prevent merge conflicts when updating from upstream.
//
// Structure:
// - config.ts: Feature flags
// - citationSanitizer.ts: Citation formatting fixes
// - useCategories.ts: Hook for fetching categories
// - DataPrivacyNotice.tsx: Data privacy information panel for users
// - __tests__/: Tests for customizations

// Feature configuration
export { CUSTOM_FEATURES, isFeatureEnabled, isAdminMode } from "./config";

// Citation sanitization
export { sanitizeCitations, fixMalformedCitations, collapseAdjacentCitations } from "./citationSanitizer";

// Category filtering
export { useCategories } from "./useCategories";
export type { Category } from "./useCategories";

// Legal Feedback
export { LegalFeedback } from "./LegalFeedback";

// External source handling
export { isIframeBlocked } from "./externalSourceHandler";

// Help & About Panel (replaces DataPrivacyNotice)
export { HelpAboutPanel } from "./HelpAboutPanel";

// Splash Screen (animated intro with morph-to-header effect)
export { SplashScreen } from "./SplashScreen";
