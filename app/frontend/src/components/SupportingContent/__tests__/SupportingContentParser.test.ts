import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { extractSubsectionContent, parseSubsectionFromCitation, parseSupportingContentItem } from "../SupportingContentParser";

const repoRoot = path.resolve(process.cwd(), "..", "..");
const citationDocPath = path.resolve(repoRoot, "changes and architecture", "CITATION_SYSTEM_FLOW.md");
const citationDocContent = readFileSync(citationDocPath, "utf-8");

const commercialGuideExcerpt = extractFullContentFromCitationDoc("A4.1 Case Management Powers");
const civilProcedureExcerpt = extractFullContentFromCitationDoc("31.1 Standard disclosure");
const commercialGuideMultiSectionBlock = extractCommercialGuideExampleBlock();

function extractFullContentFromCitationDoc(heading: string): string {
    const escapedHeading = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`"full_content":\\s*"${escapedHeading}(?:\\\\n|\n)[\\s\\S]*?"`);
    const match = citationDocContent.match(regex);
    if (!match) {
        throw new Error(`Could not find documentation excerpt for ${heading}`);
    }

    return match[0]
        .replace(/"full_content":\s*"/, "")
        .replace(/"$/, "")
        .replace(/\\n/g, "\n");
}

function extractCommercialGuideExampleBlock(): string {
    const lines = citationDocContent.split("\n");
    const start = lines.findIndex((line: string) => line.includes('"A4.1 Case Management Powers'));
    if (start === -1) {
        throw new Error("Commercial Court Guide example block not found in documentation");
    }

    let end = start;
    while (end < lines.length && !lines[end].includes("cases...")) {
        end++;
    }

    const blockLines = lines.slice(start, end + 1);
    return blockLines
        .map((line: string) => line.replace(/^\s*#\s?/, ""))
        .map((line: string) => line.replace(/^"/, ""))
        .map((line: string) => line.replace(/"$/, ""))
        .map((line: string) => line.replace(/^\s+/, ""))
        .join("\n")
        .trim();
}

describe("extractSubsectionContent", () => {
    it("captures the entire paragraph block until the next subsection marker", () => {
        const content = [
            "D5.1 Filing deadlines",
            "",
            "The parties must exchange schedules of loss before listing.",
            "Each filing should include the complete costs schedule.",
            "",
            "D5.2 Next procedural step",
            "",
            "This paragraph belongs to the next subsection."
        ].join("\n");

        const result = extractSubsectionContent(content, "D5.1");

        expect(result).not.toBeNull();
        expect(result?.startIndex).toBe(0);
        expect(result?.content).toBe(
            [
                "D5.1 Filing deadlines",
                "",
                "The parties must exchange schedules of loss before listing.",
                "Each filing should include the complete costs schedule."
            ].join("\n")
        );
        expect(result?.content.includes("\n\n")).toBe(true);
    });

    it("returns the remainder of the document when the subsection is last", () => {
        const content = [
            "C3.8 Earlier guidance",
            "",
            "This section precedes the target subsection.",
            "",
            "D5.3 Final requirements",
            "",
            "All exhibits must be bundled with dividers.",
            "The paragraph should stay highlighted entirely."
        ].join("\n");

        const result = extractSubsectionContent(content, "D5.3");

        expect(result).not.toBeNull();
        expect(result?.content).toBe(
            ["D5.3 Final requirements", "", "All exhibits must be bundled with dividers.", "The paragraph should stay highlighted entirely."].join("\n")
        );
        expect(result?.endIndex).toBe(content.length);
    });

    it("stops precisely before the next rule boundary", () => {
        const content = [
            "Rule 31.3 Disclosure order",
            "",
            "This subsection explains the obligation to disclose.",
            "It also covers timelines.",
            "",
            "Rule 31.4 Specific disclosure",
            "",
            "The next subsection starts here and should not be captured."
        ].join("\n");

        const result = extractSubsectionContent(content, "Rule 31.3");

        expect(result).not.toBeNull();
        expect(result?.content).toBe(
            ["Rule 31.3 Disclosure order", "", "This subsection explains the obligation to disclose.", "It also covers timelines."].join("\n")
        );
    });

    it("handles nested identifiers such as A1.2.3", () => {
        const content = [
            "A1.2.3 Service requirements",
            "",
            "Paragraph body lines stay grouped until a divider.",
            "",
            "---",
            "",
            "Appendix 1 Ancillary guidance"
        ].join("\n");

        const result = extractSubsectionContent(content, "A1.2.3");

        expect(result).not.toBeNull();
        expect(result?.content).toBe(["A1.2.3 Service requirements", "", "Paragraph body lines stay grouped until a divider."].join("\n"));
    });

    it("extracts Commercial Court Guide subsections from documentation", () => {
        const result = extractSubsectionContent(commercialGuideMultiSectionBlock, "A4.1");

        expect(result).not.toBeNull();
        expect(result?.content.startsWith("A4.1 Case Management Powers")).toBe(true);
        expect(result?.content).not.toContain("A4.2 Pre-Trial Review");
    });

    it("extracts CPR Part 31 subsections from documentation", () => {
        const cprDocument = [civilProcedureExcerpt, "", "31.2 Specific disclosure", "The court may order a party to take a specific step in disclosure."].join(
            "\n"
        );

        const result = extractSubsectionContent(cprDocument, "31.1");

        expect(result).not.toBeNull();
        expect(result?.content.startsWith("31.1 Standard disclosure")).toBe(true);
        expect(result?.content).not.toContain("31.2 Specific disclosure");
    });
});

describe("parseSubsectionFromCitation", () => {
    it("recognizes standard numeric citations", () => {
        expect(parseSubsectionFromCitation("D5.4, D Section, Guide.pdf")).toBe("D5.4");
    });

    it("accepts Part-prefixed subsections", () => {
        expect(parseSubsectionFromCitation("Part 36, Part 36 Offers, CPR.pdf")).toBe("Part 36");
    });

    it("accepts Rule references", () => {
        expect(parseSubsectionFromCitation("Rule 31.6, Disclosure, CPR.pdf")).toBe("Rule 31.6");
    });

    it("returns null when the format is not recognized", () => {
        expect(parseSubsectionFromCitation("Attachment, Random, File.pdf")).toBeNull();
    });
});

describe("parseSupportingContentItem", () => {
    it("preserves category metadata for structured court guide entries", () => {
        const item = {
            sourcefile: "Queen's Bench Guide.pdf",
            sourcepage: "Sec 5",
            category: "Queen's Bench Guide",
            full_content: "<script>alert('x')</script><p>All applications must follow Practice Direction.</p>"
        };

        const parsed = parseSupportingContentItem(item);

        expect(parsed.category).toBe("Queen's Bench Guide");
        expect(parsed.sourcepage).toBe("Sec 5");
        expect(parsed.title).toBe("Queen's Bench Guide.pdf");
        expect(parsed.content).toContain("All applications must follow Practice Direction.");
        expect(parsed.content).not.toContain("<script>");
    });

    it("derives category from CPR rule citation strings", () => {
        const raw = "[Rule 31.3, Civil Procedure Rules, CPR.pdf]: Disclosure timelines apply to every list.";

        const parsed = parseSupportingContentItem(raw);

        expect(parsed.sourcepage).toBe("Rule 31.3");
        expect(parsed.category).toBe("Civil Procedure Rules");
        expect(parsed.sourcefile).toBe("CPR.pdf");
        expect(parsed.title).toBe("CPR.pdf");
    });

    it("derives category from court guide citation strings", () => {
        const raw = "[Section 5, Commercial Court Guide, CommCourtGuide.pdf]: Directions hearings are scheduled weekly.";

        const parsed = parseSupportingContentItem(raw);

        expect(parsed.sourcepage).toBe("Section 5");
        expect(parsed.category).toBe("Commercial Court Guide");
        expect(parsed.sourcefile).toBe("CommCourtGuide.pdf");
    });

    it("retains metadata for documentation-backed Commercial Court excerpts", () => {
        const item = {
            sourcefile: "Circuit Commercial Court Guide",
            sourcepage: "A.4 Case Management Powers",
            category: "Circuit Commercial Court",
            full_content: commercialGuideExcerpt,
            id: "doc-com-1"
        };

        const parsed = parseSupportingContentItem(item);

        expect(parsed.category).toBe("Circuit Commercial Court");
        expect(parsed.sourcefile).toBe("Circuit Commercial Court Guide");
        expect(parsed.content).toContain("A4.1 Case Management Powers");
    });

    it("retains metadata for documentation-backed CPR excerpts", () => {
        const item = {
            sourcefile: "Part 31",
            sourcepage: "Disclosure and Inspection of Documents",
            category: "Civil Procedure Rules and Practice Directions",
            full_content: civilProcedureExcerpt,
            id: "doc-cpr-1"
        };

        const parsed = parseSupportingContentItem(item);

        expect(parsed.category).toBe("Civil Procedure Rules and Practice Directions");
        expect(parsed.sourcefile).toBe("Part 31");
        expect(parsed.content).toContain("31.1 Standard disclosure");
    });
});
