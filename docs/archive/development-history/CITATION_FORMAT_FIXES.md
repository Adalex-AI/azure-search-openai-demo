# Citation Format Fixes - November 3, 2025

## Problem Identified

The AI responses were generating malformed citations with inconsistent formats, specifically:

### Issues Found:

1. **Comma-separated citations without brackets**: `1, 2, 4, [14.6], 3, 6`
1. **Mixed bracketed and unbracketed numbers**: `1, 2, [3]` or `123[10.15]`
1. **Complex nested citations**: `123[10.15–10.17, 10.25–10.27]`
1. **Commas inside brackets**: `[1, 2, 3]`
1. **Commas between bracketed citations**: `[1], [2], [3]`

### Expected Format:

- Each citation should be a single number in its own bracket: `[1]`
- Multiple citations should be consecutive brackets with NO commas: `[1][2][3]`
- Example: "The bundle should include case summaries and draft orders [1][2]."

## Root Cause

The prompts in `chat_answer_question.prompty` and `ask_answer_question.prompty` did not explicitly forbid comma-separated citation formats, allowing the LLM to generate various incorrect formats.

## Solution Applied

### Files Modified:

1. `/app/backend/approaches/prompts/chat_answer_question.prompty`
1. `/app/backend/approaches/prompts/ask_answer_question.prompty`

### Changes Made:

Added a new **CRITICAL CITATION FORMAT RULES** section immediately after the **CRITICAL INSTRUCTIONS** section with:

1. **Explicit format requirements**:
   - Each citation MUST be a single number enclosed in square brackets
   - Multiple sources use consecutive brackets with NO commas: `[1][2][3]`

1. **Clear examples of correct formats**:

```text
   ✓ [1]
   ✓ [1][2]
   ✓ [1][2][3]
   ```

1. **Clear examples of incorrect formats (explicitly prohibited)**:

```text
   ✗ 1, 2, 3
   ✗ [1, 2, 3]
   ✗ 1, 2, [3]
   ✗ [1], [2], [3]
   ✗ 123
   ```

1. **Concrete sentence examples**:
   - ✓ "The bundle should include case summaries and draft orders [1][2]."
   - ✗ "The bundle should include case summaries and draft orders 1, 2, 3."
   - ✗ "The bundle should include case summaries and draft orders [1, 2, 3]."

## Testing Recommendations

After restarting the application, test with queries that typically return multi-source citations:

### Test Query 1:

"What documents are required for a CMC hearing bundle?"

**Expected Output**: Citations should appear as `[1][2][3]` not `1, 2, 3` or `[1, 2, 3]`

### Test Query 2:

"What are the disclosure obligations in fast track cases?"

**Expected Output**: Each sentence should end with properly formatted citations like `[1]` or `[1][2]`

## Additional Notes

- The vision prompts (`chat_answer_question_vision.prompty` and `ask_answer_question_vision.prompty`) were not modified as they serve a different use case (financial reports) with simpler citation requirements
- The frontend parsing logic in `SupportingContentParser.ts` already supports the correct `[1][2][3]` format
- No backend Python code changes were required - this was purely a prompt engineering fix

## Deployment Steps

1. Stop the running application
1. The prompt files have been updated
1. Restart the application using `./app/start.sh` or the "Start App" task
1. Test with sample queries to verify citation format
1. Monitor for any edge cases where citations might still be malformed

## Rollback Instructions

If the changes cause issues, revert by:

1. Remove the **CRITICAL CITATION FORMAT RULES** section from both prompty files
1. Keep only the original **CRITICAL INSTRUCTIONS** section
1. Restart the application
