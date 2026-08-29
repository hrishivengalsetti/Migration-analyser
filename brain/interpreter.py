import os
import json
from groq import Groq, APIError, APIConnectionError, APITimeoutError
from models import AIInterpretation, Evidence

def generate_narrative(
    diff_summary: dict,
    blast_radius_summary: dict,
    execution_summary: dict,
    evidence_data: list[Evidence]
) -> AIInterpretation:
    api_key = os.environ.get("GROQ_API_KEY")
    
    fallback = AIInterpretation(
        migration_intent="Unknown (AI interpretation unavailable).",
        risk_summary="Failed to generate AI summary due to an API, network, or validation error.",
        key_concerns=["AI interpretation failed."],
        confidence="none"
    )

    if not api_key:
        return fallback

    prompt = _build_prompt(diff_summary, blast_radius_summary, execution_summary, evidence_data)

    try:
        client = Groq(api_key=api_key, timeout=30.0)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior principal engineer reviewing a codebase migration. You provide concise, factual JSON summaries."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            return fallback

        data = json.loads(content)
        return AIInterpretation(**data)
        
    except (APIError, APIConnectionError, APITimeoutError):
        return fallback
    except (json.JSONDecodeError, ValueError):
        return fallback
    except Exception:
        return fallback


def _build_prompt(diff_summary: dict, blast_radius_summary: dict, execution_summary: dict, evidence_data: list[Evidence]) -> str:
    serialized_evidence = [
        {
            "symbol_id": e.symbol_id,
            "comparison": e.comparison,
            "failing_tests": len(e.failing_tests),
            "passing_tests": len(e.passing_tests),
            "unverified_tests": len(e.unverified_tests)
        } for e in evidence_data
    ]

    facts = {
        "diff_summary": diff_summary,
        "blast_radius_summary": blast_radius_summary,
        "execution_summary": execution_summary,
        "evidence_overview": serialized_evidence
    }

    return f"""[AUTHORITATIVE FACTS]
{json.dumps(facts, indent=2)}

[REQUIRED INTERPRETATION]
The provided [AUTHORITATIVE FACTS] are 100% deterministic and authoritative. You MUST NOT recalculate, invent, or contradict regressions, fixes, or affected symbols.

Do not invent test results, files, or symbols. Do not create new regressions or change existing classifications.
Unverified results must be described as requiring manual review.

Your [REQUIRED INTERPRETATION] is ONLY to summarize the *intent* of the migration (e.g., 'Migrating from requests to httpx') and explain the *technical risk* of the proven regressions.

Return valid JSON matching EXACTLY this schema:
{{
  "migration_intent": "string",
  "risk_summary": "string",
  "key_concerns": ["string", "string"],
  "confidence": "high" | "medium" | "low" | "none"
}}"""
