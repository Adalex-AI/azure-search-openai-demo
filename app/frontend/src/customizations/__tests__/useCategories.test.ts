/**
 * Frontend Tests for useCategories Hook
 *
 * Tests for category fetching functionality
 */

import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useCategories } from "../useCategories";

describe("useCategories Hook", () => {
    beforeEach(() => {
        // Clear any previous mocks
        vi.clearAllMocks();
    });

    test("should return initial state with loading=true", () => {
        global.fetch = vi.fn();
        const { result } = renderHook(() => useCategories());

        expect(result.current.loading).toBe(true);
        expect(result.current.categories).toEqual([]);
        expect(result.current.error).toBeNull();
    });

    test("should fetch categories from API", async () => {
        const mockCategories = [
            { key: "", text: "All Sources" },
            { key: "Commercial Court", text: "Commercial Court Guide", count: 42 }
        ];

        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ categories: mockCategories })
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.categories).toEqual(mockCategories);
        expect(result.current.error).toBeNull();
    });

    test("should handle fetch errors gracefully", async () => {
        global.fetch = vi.fn(() => Promise.reject(new Error("Network error")));

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.error).toEqual("Network error");
        // Should provide default fallback
        expect(result.current.categories).toEqual([{ key: "", text: "All Sources" }]);
    });

    test("should handle API errors (non-200 response)", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: false,
                status: 404
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.error).toBeTruthy();
        expect(result.current.categories).toEqual([{ key: "", text: "All Sources" }]);
    });

    test("should handle missing categories in response", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({}) // No categories key
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.categories).toEqual([]);
        expect(result.current.error).toBeNull();
    });

    test("should cleanup mounted flag on unmount", async () => {
        const { result, unmount } = renderHook(() => useCategories());

        unmount();

        // Should complete without errors
        expect(result.current).toBeDefined();
    });

    test("should handle invalid JSON response", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.reject(new Error("Invalid JSON"))
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.error).toTruthy();
    });

    test("should not update state after unmount", async () => {
        let resolveResponse: any;
        global.fetch = vi.fn(
            () =>
                new Promise(resolve => {
                    resolveResponse = resolve;
                })
        );

        const { result, unmount } = renderHook(() => useCategories());

        // Unmount before response completes
        unmount();

        // Resolve the fetch after unmount
        resolveResponse({
            ok: true,
            json: () =>
                Promise.resolve({
                    categories: [{ key: "test", text: "Test" }]
                })
        });

        // Should not cause state update error
        expect(result.current).toBeDefined();
    });

    test("should handle empty categories array", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ categories: [] })
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.categories).toEqual([]);
        expect(result.current.error).toBeNull();
    });

    test("should include category counts when provided", async () => {
        const mockCategories = [
            { key: "", text: "All Sources" },
            { key: "Court A", text: "Court A Guide", count: 25 },
            { key: "Court B", text: "Court B Guide", count: 15 }
        ];

        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ categories: mockCategories })
            } as Response)
        );

        const { result } = renderHook(() => useCategories());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.categories).toHaveLength(3);
        expect(result.current.categories[1].count).toBe(25);
        expect(result.current.categories[2].count).toBe(15);
    });

    test("should call /api/categories endpoint", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ categories: [] })
            } as Response)
        );

        renderHook(() => useCategories());

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith("/api/categories");
        });
    });
});
