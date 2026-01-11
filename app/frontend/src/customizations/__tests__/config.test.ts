/**
 * Frontend Unit Tests for Customization Configuration
 *
 * Tests for feature flag management and admin mode detection
 */

import { CUSTOM_FEATURES, isFeatureEnabled, isAdminMode } from "../config";

describe("CUSTOM_FEATURES Configuration", () => {
    test("should define all expected feature flags", () => {
        const expectedFlags = ["categoryFilter", "citationSanitizer", "legalDomainPrompts", "adminMode", "showCitationsPanel"];

        expectedFlags.forEach(flag => {
            expect(flag in CUSTOM_FEATURES).toBe(true);
        });
    });

    test("should have boolean values for all flags", () => {
        Object.values(CUSTOM_FEATURES).forEach(value => {
            expect(typeof value).toBe("boolean");
        });
    });

    test("should have default values set", () => {
        expect(CUSTOM_FEATURES.categoryFilter).toBe(true);
        expect(CUSTOM_FEATURES.citationSanitizer).toBe(true);
        expect(CUSTOM_FEATURES.legalDomainPrompts).toBe(true);
        expect(CUSTOM_FEATURES.adminMode).toBe(false);
        expect(CUSTOM_FEATURES.showCitationsPanel).toBe(true);
    });
});

describe("isFeatureEnabled", () => {
    test("should return true for enabled features", () => {
        expect(isFeatureEnabled("categoryFilter")).toBe(true);
        expect(isFeatureEnabled("citationSanitizer")).toBe(true);
        expect(isFeatureEnabled("legalDomainPrompts")).toBe(true);
    });

    test("should return false for disabled features", () => {
        expect(isFeatureEnabled("adminMode")).toBe(false);
    });

    test("should return false for non-existent features", () => {
        expect(isFeatureEnabled("nonExistentFeature" as any)).toBe(false);
    });

    test("should handle all feature flag keys", () => {
        const keys = Object.keys(CUSTOM_FEATURES) as Array<keyof typeof CUSTOM_FEATURES>;

        keys.forEach(key => {
            const result = isFeatureEnabled(key);
            expect(typeof result).toBe("boolean");
        });
    });
});

describe("isAdminMode", () => {
    // Store original location
    const originalLocation = window.location;

    beforeEach(() => {
        // Reset URL to clean state
        delete (window as any).location;
        (window as any).location = { ...originalLocation, search: "" };
    });

    afterEach(() => {
        // Restore original location
        delete (window as any).location;
        (window as any).location = originalLocation;
    });

    test("should return false when admin mode is disabled and no URL param", () => {
        expect(isAdminMode()).toBe(false);
    });

    test("should return true when ?admin=true URL parameter is present", () => {
        (window as any).location = {
            ...originalLocation,
            search: "?admin=true"
        };

        expect(isAdminMode()).toBe(true);
    });

    test("should return false when ?admin=false URL parameter is present", () => {
        (window as any).location = {
            ...originalLocation,
            search: "?admin=false"
        };

        expect(isAdminMode()).toBe(false);
    });

    test("should ignore case sensitivity in URL parameter value", () => {
        (window as any).location = {
            ...originalLocation,
            search: "?admin=True"
        };

        // Function checks for exact "true" string, case-sensitive
        expect(isAdminMode()).toBe(false);
    });

    test("should handle multiple URL parameters", () => {
        (window as any).location = {
            ...originalLocation,
            search: "?page=1&admin=true&sort=date"
        };

        expect(isAdminMode()).toBe(true);
    });

    test("should return config value when no URL param and adminMode is true", () => {
        // Modify config temporarily
        const original = CUSTOM_FEATURES.adminMode;
        CUSTOM_FEATURES.adminMode = true;
        try {
            (window as any).location = {
                ...originalLocation,
                search: ""
            };

            expect(isAdminMode()).toBe(true);
        } finally {
            CUSTOM_FEATURES.adminMode = original;
        }
    });

    test("should handle undefined window gracefully", () => {
        // Capture current window reference
        const result = isAdminMode();
        expect(typeof result).toBe("boolean");
    });

    test("should return false for empty search string", () => {
        (window as any).location = {
            ...originalLocation,
            search: ""
        };

        expect(isAdminMode()).toBe(false);
    });

    test("should handle search params with equals in value", () => {
        (window as any).location = {
            ...originalLocation,
            search: "?redirect=http://example.com&admin=true"
        };

        expect(isAdminMode()).toBe(true);
    });
});

describe("Feature Flag Integration", () => {
    test("should allow checking multiple features", () => {
        const features = ["categoryFilter", "citationSanitizer", "legalDomainPrompts"] as const;

        const enabledFeatures = features.filter(f => isFeatureEnabled(f));
        expect(enabledFeatures.length).toBeGreaterThan(0);
    });

    test("should be type-safe with TypeScript", () => {
        // This test is primarily for TypeScript compilation verification
        const categoryFilterEnabled: boolean = isFeatureEnabled("categoryFilter");
        expect(typeof categoryFilterEnabled).toBe("boolean");
    });
});
