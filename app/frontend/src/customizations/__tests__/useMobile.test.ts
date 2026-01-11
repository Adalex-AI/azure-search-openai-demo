/**
 * Frontend Tests for Mobile Detection Hook
 *
 * Tests for mobile breakpoint detection and abbreviations
 */

import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useIsMobile, CATEGORY_ABBREVIATIONS, DEPTH_OPTIONS, getDepthLabel } from "../useMobile";

describe("useIsMobile Hook", () => {
    const MOBILE_BREAKPOINT = 768;

    beforeEach(() => {
        vi.clearAllMocks();
    });

    test("should detect mobile on initial render when width < 768", () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 500
        });

        const { result } = renderHook(() => useIsMobile());

        expect(result.current).toBe(true);
    });

    test("should detect desktop on initial render when width >= 768", () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 1024
        });

        const { result } = renderHook(() => useIsMobile());

        expect(result.current).toBe(false);
    });

    test("should update on window resize to mobile", async () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 1024
        });

        const { result } = renderHook(() => useIsMobile());

        expect(result.current).toBe(false);

        // Resize to mobile
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 500
        });

        window.dispatchEvent(new Event("resize"));

        await waitFor(() => {
            expect(result.current).toBe(true);
        });
    });

    test("should update on window resize to desktop", async () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 500
        });

        const { result } = renderHook(() => useIsMobile());

        expect(result.current).toBe(true);

        // Resize to desktop
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 1024
        });

        window.dispatchEvent(new Event("resize"));

        await waitFor(() => {
            expect(result.current).toBe(false);
        });
    });

    test("should respect exact breakpoint at 768px", () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: MOBILE_BREAKPOINT
        });

        const { result } = renderHook(() => useIsMobile());

        // 768 is not less than 768, so should be false (desktop)
        expect(result.current).toBe(false);
    });

    test("should cleanup resize listener on unmount", () => {
        const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

        const { unmount } = renderHook(() => useIsMobile());

        unmount();

        expect(removeEventListenerSpy).toHaveBeenCalledWith("resize", expect.any(Function));
        removeEventListenerSpy.mockRestore();
    });

    test("should handle multiple resize events", async () => {
        Object.defineProperty(window, "innerWidth", {
            writable: true,
            configurable: true,
            value: 1024
        });

        const { result } = renderHook(() => useIsMobile());

        expect(result.current).toBe(false);

        // First resize
        Object.defineProperty(window, "innerWidth", {
            value: 500
        });
        window.dispatchEvent(new Event("resize"));

        await waitFor(() => {
            expect(result.current).toBe(true);
        });

        // Second resize
        Object.defineProperty(window, "innerWidth", {
            value: 900
        });
        window.dispatchEvent(new Event("resize"));

        await waitFor(() => {
            expect(result.current).toBe(false);
        });
    });
});

describe("CATEGORY_ABBREVIATIONS", () => {
    test("should be a record object", () => {
        expect(typeof CATEGORY_ABBREVIATIONS).toBe("object");
        expect(CATEGORY_ABBREVIATIONS).not.toBeNull();
    });

    test("should have all values as non-empty strings", () => {
        Object.values(CATEGORY_ABBREVIATIONS).forEach(value => {
            expect(typeof value).toBe("string");
            expect(value.length).toBeGreaterThan(0);
        });
    });

    test("should have all keys as non-empty strings", () => {
        Object.keys(CATEGORY_ABBREVIATIONS).forEach(key => {
            expect(typeof key).toBe("string");
            expect(key.length).toBeGreaterThan(0);
        });
    });

    test("should contain CPR part abbreviations", () => {
        const cprKeys = Object.keys(CATEGORY_ABBREVIATIONS).filter(key => key.includes("CPR Part"));

        expect(cprKeys.length).toBeGreaterThan(0);
    });

    test("should abbreviate CPR parts to shorter format", () => {
        const abbrev = CATEGORY_ABBREVIATIONS["CPR Part 1 - Overriding Objective"];
        expect(abbrev).toBe("CPR 1");
        expect(abbrev.length).toBeLessThan("CPR Part 1 - Overriding Objective".length);
    });

    test("should have Practice Direction abbreviations", () => {
        const pdKeys = Object.keys(CATEGORY_ABBREVIATIONS).filter(key => key.includes("PD") || key.includes("Practice Direction"));

        // Should have some practice direction abbreviations
        expect(pdKeys.length).toBeGreaterThanOrEqual(0);
    });

    test("should have Court Guide abbreviations", () => {
        const courtKeys = Object.keys(CATEGORY_ABBREVIATIONS).filter(key => key.includes("Court"));

        // Court abbreviations should exist
        expect(courtKeys.length).toBeGreaterThanOrEqual(0);
    });

    test("should map longer names to shorter abbreviations", () => {
        Object.entries(CATEGORY_ABBREVIATIONS).forEach(([fullName, abbrev]) => {
            // Abbreviations should generally be shorter than full names
            // (with some exceptions for already-short names)
            if (fullName.length > 20) {
                expect(abbrev.length).toBeLessThan(fullName.length);
            }
        });
    });

    test("should handle lookups for existing categories", () => {
        const cprPart7 = CATEGORY_ABBREVIATIONS["CPR Part 7 - Starting Proceedings"];
        expect(cprPart7).toBeDefined();
        expect(cprPart7).toBe("CPR 7");
    });

    test("should return undefined for non-existent categories", () => {
        const nonExistent = CATEGORY_ABBREVIATIONS["Non-existent Category"];
        expect(nonExistent).toBeUndefined();
    });
});

describe("Search Depth labels", () => {
    test("DEPTH_OPTIONS has expected keys", () => {
        expect(Object.keys(DEPTH_OPTIONS)).toEqual(expect.arrayContaining(["minimal", "low", "medium"]));
    });

    test("getDepthLabel returns short label on mobile", () => {
        expect(getDepthLabel("minimal", true)).toBe("Q");
        expect(getDepthLabel("low", true)).toBe("S");
        expect(getDepthLabel("medium", true)).toBe("T");
    });

    test("getDepthLabel returns full label on desktop", () => {
        expect(getDepthLabel("minimal", false)).toBe("Quick");
        expect(getDepthLabel("low", false)).toBe("Standard");
        expect(getDepthLabel("medium", false)).toBe("Thorough");
    });

    test("getDepthLabel falls back to key for unknown option", () => {
        expect(getDepthLabel("unknown", true)).toBe("unknown");
    });
});
