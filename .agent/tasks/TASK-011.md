# TASK-011: AI Interpreter — Gemini Flash Integration & Prompt Template

**Milestone**: M7  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-010B (complete)  

---

## Goal

Integrate Google Gemini Flash via the `google-generativeai` SDK to generate a narrative migration summary. The interpreter receives a condensed summary of the analysis results and produces a structured interpretation with migration intent, risk summary, key concerns, and confidence level. The interpreter MUST fail gracefully — if the API key is missing or the call fails, it returns a fallback object and does NOT crash the pipeline.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 7: AI Interpretation)
3. `backend/models.py`
4. `backend/pipeline/evidence.py` (from TASK-010A)
5. This task file

---

## Inputs

- Summary data dict containing: file diffs count, symbol diffs count, blast radius size, regression count, evidence summary, classification result

## Outputs

```
backend/prompts/interpreter.txt      ← New file
backend/pipeline/interpreter.py      ← New file
backend/tests/test_interpreter.py    ← New file
backend/requirements.txt             ← Updated: add google-generativeai
```

---

## Data Models (use from models.py — already defined)

```python
class AIInterpretation(BaseModel):
    migration_intent: str
    risk_summary: str
    key_concerns: list[str]
    confidence: str
```

---

## Acceptance Criteria

### AC-1: Prompt template
- `backend/prompts/interpreter.txt` exists and contains a structured prompt
- The prompt instructs the model to return a JSON object with exactly these fields:
  - `migration_intent`: 1-2 sentence summary of what the migration appears to do
  - `risk_summary`: 1-2 sentence assessment of migration risk
  - `key_concerns`: list of up to 5 bullet-point concerns
  - `confidence`: one of "high", "medium", "low"
- The prompt includes the analysis data as context

### AC-2: Function signature
```python
def interpret_migration(
    file_diffs_count: int,
    symbol_diffs_count: int,
    blast_radius_count: int,
    regression_count: int,
    classification: str,
    changed_symbols: list[str],
    evidence_summary: list[dict],
) -> AIInterpretation:
    ...
```

### AC-3: Gemini Flash integration
- Uses `google.generativeai` SDK
- Loads API key from environment variable `GEMINI_API_KEY`
- Uses model `gemini-2.0-flash` (or `gemini-1.5-flash` if unavailable)
- Sends one API call with the formatted prompt
- Parses the response JSON into `AIInterpretation`

### AC-4: Graceful fallback — missing API key
- If `GEMINI_API_KEY` is not set in environment:
  - Does NOT raise an exception
  - Returns a default `AIInterpretation` with:
    ```python
    AIInterpretation(
        migration_intent="AI interpretation unavailable — no API key configured.",
        risk_summary="Unable to assess risk without AI analysis.",
        key_concerns=["Configure GEMINI_API_KEY environment variable for AI-powered analysis."],
        confidence="low",
    )
    ```

### AC-5: Graceful fallback — API error
- If the API call fails (network error, invalid key, rate limit, timeout, etc.):
  - Catches the exception
  - Logs the error (print or logging module)
  - Returns the same fallback `AIInterpretation` as AC-4
  - Does NOT crash the pipeline

### AC-6: Graceful fallback — malformed response
- If the model returns text that cannot be parsed as JSON:
  - Attempts to extract JSON from the response text (look for `{...}`)
  - If extraction fails, returns fallback `AIInterpretation`

### AC-7: One call per run
- The function makes exactly ONE API call to Gemini per invocation
- There is no retry loop or multi-call strategy

### AC-8: All tests pass
- `cd backend && pytest tests/test_interpreter.py -v` exits with code 0

---

## Non-Goals

- Do NOT use AI for classification (classification is deterministic in TASK-010A)
- Do NOT make multiple AI calls
- Do NOT implement streaming responses
- Do NOT implement prompt engineering beyond the basic template
- Do NOT cache AI responses
- Do NOT integrate into `runner.py` yet (that is TASK-012)

---

## Technical Constraints

- `google-generativeai` package (add to `backend/requirements.txt`)
- Environment variable: `GEMINI_API_KEY`
- Model: `gemini-2.0-flash` (or fallback to `gemini-1.5-flash`)
- Max 1 API call per pipeline run

---

## Prompt Template

Create `backend/prompts/interpreter.txt`:

```
You are a software migration analysis expert. You are given the results of a deterministic code migration analysis comparing an original Python codebase to a migrated version.

Analyze the following migration data and provide a structured assessment.

## Migration Analysis Data

- Files changed: {files_changed}
- Symbols changed: {symbols_changed}
- Blast radius (affected symbols): {blast_radius_count}
- Regressions detected: {regression_count}
- Classification: {classification}

### Changed Symbols
{changed_symbols_list}

### Evidence Summary
{evidence_summary}

## Required Response Format

Respond with ONLY a JSON object (no markdown, no code fences) with exactly these fields:

{
  "migration_intent": "1-2 sentence description of what this migration appears to accomplish",
  "risk_summary": "1-2 sentence assessment of the migration's risk level based on the evidence",
  "key_concerns": ["concern 1", "concern 2", "up to 5 specific concerns"],
  "confidence": "high" | "medium" | "low"
}
```

---

## Test Requirements

Write tests in `backend/tests/test_interpreter.py`:

**All tests must mock the external API call. Do NOT make real API calls in tests.**

```python
from unittest.mock import patch, MagicMock
```

1. `test_returns_ai_interpretation_on_success` — mock successful API response with valid JSON → returns populated `AIInterpretation`
2. `test_fallback_when_no_api_key` — mock `os.environ` without `GEMINI_API_KEY` → returns fallback object
3. `test_fallback_on_api_error` — mock API call raising an exception → returns fallback object, no crash
4. `test_fallback_on_malformed_response` — mock API returning non-JSON text → returns fallback object
5. `test_extracts_json_from_markdown_fences` — mock API returning JSON wrapped in ```json ... ``` → correctly parses
6. `test_single_api_call` — mock API call → verify it was called exactly once

---

## Verification

```bash
cd backend && pytest tests/test_interpreter.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
