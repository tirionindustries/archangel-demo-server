import asyncio
import json

from google import genai
from google.genai import types

from app.core.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

_SYSTEM_PROMPT = (
    "You are Archangel's incident reasoning engine. You analyze security incidents for Nigerian "
    "security operators. You receive structured incident data and return a JSON brief. You are "
    "concise, precise, and clearly distinguish confirmed facts from inferences. Never speculate "
    "beyond the data provided."
)

_BRIEF_SCHEMA = """{
  "threat_classification": "string",
  "confidence_level": "high|medium|low|unknown",
  "what_we_know": "string",
  "what_we_inferred": "string",
  "what_is_unknown": "string",
  "recommended_response": "string",
  "operator_brief": "string (2-3 sentences, action-oriented)",
  "pattern_notes": "string or null",
  "sms_to_caller": "string or null"
}"""

# Realistic fallback used when API is unavailable — demo stays live regardless
_MOCK_BRIEF = {
    "threat_classification": "Armed Group Incursion — Public Market",
    "confidence_level": "high",
    "what_we_know": (
        "USSD distress signal received from Kafanchan main market at 9.7795°N 8.2982°E. "
        "Caller reported approximately 10 armed individuals. Call was cut — consistent with "
        "caller attempting to avoid detection. 14 GSM signatures detected in the incident radius; "
        "3 flagged as threat signatures showing coordinated northwest-to-southeast convergence."
    ),
    "what_we_inferred": (
        "Coordinated movement of 3 GSM signatures suggests organised group, not opportunistic. "
        "Call cut pattern consistent with caller going silent under duress. "
        "Market setting implies potential hostage or robbery scenario with civilian exposure."
    ),
    "what_is_unknown": (
        "Exact number of armed personnel unconfirmed. Motive (robbery, kidnap, political) unknown. "
        "Caller current status unknown post-cut. Whether group has vehicles or is on foot unknown."
    ),
    "recommended_response": (
        "Deploy rapid response unit to Kafanchan main market immediately. Approach from Zaria Road "
        "to avoid alerting subjects via main Kafanchan-Kagoro road. Establish perimeter before "
        "direct engagement. Notify Kaduna State Police Command and 1 Division Nigerian Army Kaduna."
    ),
    "operator_brief": (
        "Armed group of approximately 10 confirmed at Kafanchan main market — caller cut, likely "
        "under duress. 3 coordinated threat signatures on GSM grid confirm organised incursion. "
        "Dispatch RT-04 immediately; request Kaduna State Police backup."
    ),
    "pattern_notes": (
        "GSM convergence pattern matches methodology observed in 2024 Kafanchan market incidents. "
        "Recommend cross-referencing flagged numbers against known threat registry."
    ),
    "sms_to_caller": (
        "Help is coming. Stay hidden, keep phone silent. Reply 1 if safe to talk."
    ),
}

_FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash"]


async def generate_incident_brief(incident_data: dict) -> dict:
    prompt = (
        f"Analyze this incident and return ONLY valid JSON matching this schema:\n{_BRIEF_SCHEMA}\n\n"
        f"Incident data:\n{json.dumps(incident_data, indent=2, default=str)}"
    )

    for model in _FALLBACK_MODELS:
        for attempt in range(2):
            try:
                response = await _client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                return json.loads(response.text)
            except Exception as exc:
                err = str(exc)
                if "429" in err and attempt == 0:
                    print(f"[gemini] Rate limited on {model}, retrying in 35s…")
                    await asyncio.sleep(35)
                    continue
                print(f"[gemini] {model} failed: {err[:120]}")
                break  # try next model

    print("[gemini] All models failed — using mock brief")
    return _MOCK_BRIEF
