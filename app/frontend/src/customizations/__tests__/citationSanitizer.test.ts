/**
 * CUSTOM CITATION SANITIZER TESTS
 * ================================
 * Tests for the citation sanitization logic.
 * These tests are independent of upstream and will continue to work after merges.
 */

import { describe, expect, it } from "vitest";
import { fixMalformedCitations, collapseAdjacentCitations, sanitizeCitations } from "../citationSanitizer";

describe("fixMalformedCitations", () => {
    it("fixes duplicated number pattern like '1. 1' → '[1]'", () => {
        expect(fixMalformedCitations("The answer is here 1. 1")).toBe("The answer is here [1]");
    });

    it("fixes duplicated pattern at end of sentence", () => {
        expect(fixMalformedCitations("See the disclosure 1. 1 for details")).toBe("See the disclosure [1] for details");
    });

    it("fixes duplicated pattern WITHOUT space like '1.1' → '[1]'", () => {
        expect(fixMalformedCitations("The answer is here 1.1")).toBe("The answer is here [1]");
    });

    it("fixes duplicated no-space pattern at end of text", () => {
        expect(fixMalformedCitations("...at proportionate cost 1.1")).toBe("...at proportionate cost [1]");
    });

    it("fixes bracketed duplicates like '[1].[1]' → '[1]'", () => {
        expect(fixMalformedCitations("The result [1].[1]")).toBe("The result [1]");
    });

    it("fixes bracketed duplicates without period like '[1][1]' → '[1]'", () => {
        expect(fixMalformedCitations("The result [1][1]")).toBe("The result [1]");
    });

    it("fixes multiple duplicated patterns in same text", () => {
        expect(fixMalformedCitations("First point 1. 1 and second point 2. 2")).toBe("First point [1] and second point [2]");
    });

    it("fixes multiple no-space duplicates in same text", () => {
        expect(fixMalformedCitations("First point 1.1 and second 2.2")).toBe("First point [1] and second [2]");
    });

    it("handles larger citation numbers", () => {
        expect(fixMalformedCitations("Reference 45. 45 in the guide")).toBe("Reference [45] in the guide");
    });

    it("does not modify valid decimal numbers like 3.14", () => {
        expect(fixMalformedCitations("The value is 3.14 and 2.5")).toBe("The value is 3.14 and 2.5");
    });

    it("does not modify non-duplicated patterns like 1.2", () => {
        expect(fixMalformedCitations("Section 1.2 covers this")).toBe("Section 1.2 covers this");
    });

    it("does not modify non-duplicated patterns with space", () => {
        expect(fixMalformedCitations("Section 1. 2 and 3. 4")).toBe("Section 1. 2 and 3. 4");
    });

    it("fixes unbracketed citation at end of text", () => {
        expect(fixMalformedCitations("...the proceedings 1.")).toBe("...the proceedings.[1]");
    });

    it("does not fix unbracketed number mid-sentence", () => {
        // Only fix at true end of text to avoid false positives
        expect(fixMalformedCitations("...the proceedings 2. The next")).toBe("...the proceedings 2. The next");
    });

    it("fixes unbracketed citation at paragraph end", () => {
        expect(fixMalformedCitations("First paragraph ends here 1.")).toBe("First paragraph ends here.[1]");
    });

    it("does not modify section numbers like 3.1 mid-sentence", () => {
        expect(fixMalformedCitations("See section 3.1 for details")).toBe("See section 3.1 for details");
    });

    it("fixes range citations with en-dash", () => {
        expect(fixMalformedCitations("See rules [69–81] for details")).toBe("See rules [69] for details");
    });

    it("fixes range citations with hyphen", () => {
        expect(fixMalformedCitations("See rules [69-81] for details")).toBe("See rules [69] for details");
    });
});

describe("collapseAdjacentCitations", () => {
    it("collapses adjacent citations to keep last one", () => {
        expect(collapseAdjacentCitations("Text [1][2]")).toBe("Text [2]");
    });

    it("handles multiple adjacent citations", () => {
        expect(collapseAdjacentCitations("Text [1][2][3]")).toBe("Text [3]");
    });

    it("handles repeated same citations", () => {
        expect(collapseAdjacentCitations("Text [1][1][1]")).toBe("Text [1]");
    });

    it("preserves non-adjacent citations", () => {
        expect(collapseAdjacentCitations("Text [1] and more [2]")).toBe("Text [1] and more [2]");
    });
});

describe("sanitizeCitations", () => {
    it("applies both fixes in correct order", () => {
        // First fixes "1. 1" to "[1]", then if there were adjacent would collapse them
        expect(sanitizeCitations("Text 1. 1")).toBe("Text [1]");
    });

    it("handles complex mixed patterns", () => {
        const input = "First point 1. 1 and see [2][3] for more";
        const expected = "First point [1] and see [3] for more";
        expect(sanitizeCitations(input)).toBe(expected);
    });
});
