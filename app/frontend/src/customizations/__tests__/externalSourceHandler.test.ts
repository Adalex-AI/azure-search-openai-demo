import { describe, it, expect } from "vitest";
import { isIframeBlocked } from "../externalSourceHandler";

describe("isIframeBlocked", () => {
    it("returns false for empty url", () => {
        expect(isIframeBlocked("")).toBe(false);
    });

    it("blocks exact known domains", () => {
        expect(isIframeBlocked("https://www.justice.gov.uk/some/path")).toBe(true);
        expect(isIframeBlocked("https://justice.gov.uk/some/path")).toBe(true);
        expect(isIframeBlocked("https://www.legislation.gov.uk/")).toBe(true);
        expect(isIframeBlocked("https://legislation.gov.uk/")).toBe(true);
    });

    it("blocks subdomains of known domains", () => {
        expect(isIframeBlocked("https://sub.justice.gov.uk/doc")).toBe(true);
        expect(isIframeBlocked("https://foo.bar.legislation.gov.uk/doc")).toBe(true);
    });

    it("does not block unrelated domains", () => {
        expect(isIframeBlocked("https://example.com/")).toBe(false);
        expect(isIframeBlocked("https://notjustice.gov.uk.evil.com/")).toBe(false);
    });

    it("returns false for invalid urls", () => {
        expect(isIframeBlocked("not a url")).toBe(false);
    });
});
