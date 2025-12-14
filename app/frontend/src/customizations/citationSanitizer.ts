/**
 * CUSTOM CITATION SANITIZER
 * =========================
 * This file contains all custom citation formatting logic.
 * It's designed to be merge-safe - upstream updates won't touch this file.
 *
 * To apply after upstream merge:
 * 1. Import sanitizeCitations from this file in AnswerParser.tsx
 * 2. Call sanitizeCitations(answerText) before parsing
 *
 * @author Your Name
 * @created 2025-12-14
 */

const ADJACENT_CITATIONS_REGEX = /\[\d+\](?:\s*\[\d+\])+/g;

/**
 * Collapse adjacent bracketed citations like [1][2] or [45][45] to keep only the last one.
 * This prevents the UI from showing multiple redundant citation superscripts.
 */
export function collapseAdjacentCitations(text: string): string {
    return text.replace(ADJACENT_CITATIONS_REGEX, match => {
        const numbers = match.match(/\d+/g);
        if (!numbers || numbers.length === 0) {
            return match;
        }
        const lastCitation = numbers[numbers.length - 1];
        return `[${lastCitation}]`;
    });
}

/**
 * Fix malformed citation patterns where the model outputs unbracketed or incorrectly formatted citations.
 *
 * Patterns fixed:
 * - "1. 1" → "[1]" (duplicated source number without brackets)
 * - "proceedings 1." → "proceedings.[1]" (unbracketed citation at end of paragraph)
 * - "[69–81]" → "[69]" (range citations - take first number only)
 * - "[69-81]" → "[69]" (range with regular hyphen)
 *
 * This handles cases where the LLM gets confused between document paragraph numbers
 * (like "1.1", "1.2") and citation indices.
 */
export function fixMalformedCitations(text: string): string {
    let result = text;

    // 1. Fix duplicated citation pattern: "N. N" where both numbers are identical
    // e.g., "...disclosure 1. 1" → "...disclosure [1]"
    const duplicatedCitationPattern = /(\s)(\d{1,3})\.\s*\2(?=\s|$|[.,;:!?)\]])/g;
    result = result.replace(duplicatedCitationPattern, (_, prefix, num) => {
        return `${prefix}[${num}]`;
    });

    // 2. Fix unbracketed citation ONLY at end of text (paragraph ending)
    // e.g., "...proceedings 1." at end → "...proceedings.[1]"
    // Only match if it's truly at the end ($ anchor) to avoid false positives
    // Must be preceded by at least 3 word characters to avoid matching "Section 1."
    const unbracketedEndPattern = /(\w{3,})\s+(\d{1,3})\.$/g;
    result = result.replace(unbracketedEndPattern, (_, word, num) => {
        return `${word}.[${num}]`;
    });

    // 3. Fix range citations: "[N–M]" or "[N-M]" → "[N]" (take first number only)
    // Uses both en-dash (–) and regular hyphen (-)
    const rangeCitationPattern = /\[(\d{1,3})[–\-]\d{1,3}\]/g;
    result = result.replace(rangeCitationPattern, (_, firstNum) => {
        return `[${firstNum}]`;
    });

    return result;
}

/**
 * Main sanitization function - applies all citation fixes in the correct order.
 * Call this on the raw LLM response before parsing into HTML.
 */
export function sanitizeCitations(text: string): string {
    // First fix malformed unbracketed citations like "1. 1" → "[1]"
    let result = fixMalformedCitations(text);
    // Then collapse any adjacent bracketed citations like [1][2] → [2]
    result = collapseAdjacentCitations(result);
    return result;
}

/**
 * INTEGRATION INSTRUCTIONS
 * ========================
 *
 * After merging upstream updates, add this import to AnswerParser.tsx:
 *
 *   import { sanitizeCitations } from "../../customizations/citationSanitizer";
 *
 * Then find where answerText is first used and wrap it:
 *
 *   const sanitizedAnswer = sanitizeCitations(answerText);
 *
 * Use sanitizedAnswer for all subsequent processing.
 */
