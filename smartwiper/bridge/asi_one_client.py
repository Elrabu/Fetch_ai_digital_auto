# bridge/asi_one_client.py
from __future__ import annotations
from dataclasses import dataclass

import json
import os
import re
import uuid
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

@dataclass
class AsiOneVerdict:
    risk_level: str          # LOW | MEDIUM | HIGH
    assessment: str
    recommended_action: str  # STOP_WIPER | KEEP_WIPER | REDUCE_WIPER

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ASI1_URL = "https://api.asi1.ai/v1/chat/completions"
ASI1_MODEL = os.environ.get("ASI1_MODEL", "asi1-mini")
ASI1_TIMEOUT_S = float(os.environ.get("ASI1_TIMEOUT_S", "20"))

# Single canonical env var. Strip quotes/whitespace defensively.
ASI1_API_KEY = (
    os.environ.get("ASI1_API_KEY", "")
    .strip()
    .strip('"')
    .strip("'")
)

if not ASI1_API_KEY:
    raise RuntimeError(
        "ASI1_API_KEY is not set. Ensure it exists in .env and that "
        "load_dotenv() runs BEFORE 'bridge.asi_one_client' is imported."
    )

log.info(
    "[asi_one] configured model=%s key_len=%d key_prefix=%s",
    ASI1_MODEL, len(ASI1_API_KEY), ASI1_API_KEY[:6],
)

# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = (
    "You are a vehicle safety supervisor for a windshield wiper system. "
    "Given the hood state, current wiper mode, and vehicle speed, decide a "
    "safe action. You MUST respond with a single JSON object and nothing "
    'else, of the form: {"action": "<ALLOW|STOP_WIPER|REDUCE_SPEED>", '
    '"reason": "<short explanation>"}. '
    "Rules: If the hood is open, the wipers must not run -> STOP_WIPER. "
    "If vehicle speed is unsafe for the wiper mode, choose REDUCE_SPEED. "
    "Otherwise ALLOW."
)

VALID_ACTIONS = {"ALLOW", "STOP_WIPER", "REDUCE_SPEED"}


def _user_prompt(hood_is_open: bool, wiper_mode: str, speed: float) -> str:
    return (
        f"hood_is_open={hood_is_open}, "
        f"current_wiper_mode={wiper_mode}, "
        f"vehicle_speed={speed}"
    )


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #

def _headers(session_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {ASI1_API_KEY}",
        "Content-Type": "application/json",
        "x-session-id": session_id,
    }


# --------------------------------------------------------------------------- #
# Response parsing
# --------------------------------------------------------------------------- #

_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_agent_text(text: str) -> dict[str, Any]:
    """
    Extract the first JSON object from the model's reply and validate it.
    Raises ValueError if no valid verdict can be parsed.
    """
    if not text or not text.strip():
        raise ValueError("ASI:One returned empty content.")

    match = _JSON_OBJ_RE.search(text)
    if not match:
        raise ValueError(f"No JSON object found in ASI:One reply: {text!r}")

    try:
        verdict = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in ASI:One reply: {text!r}") from e

    action = verdict.get("action")
    if action not in VALID_ACTIONS:
        raise ValueError(
            f"Invalid 'action' in verdict (got {action!r}); "
            f"must be one of {sorted(VALID_ACTIONS)}."
        )

    verdict.setdefault("reason", "")
    return verdict


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

async def ask_via_asi_one(
    hood_is_open: bool,
    current_wiper_mode: str,
    vehicle_speed: float,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Query ASI:One for a safety verdict. Returns a dict:
        {"action": "...", "reason": "..."}
    Raises RuntimeError on API/transport errors, ValueError on parse errors.
    """
    session_id = session_id or str(uuid.uuid4())

    payload = {
        "model": ASI1_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _user_prompt(
                    hood_is_open, current_wiper_mode, vehicle_speed
                ),
            },
        ],
        "temperature": 0,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=ASI1_TIMEOUT_S) as client:
        try:
            r = await client.post(
                ASI1_URL, json=payload, headers=_headers(session_id)
            )
            logging.info("[asi_one] raw status=%s body_prefix=%s", r.status_code, r.text[:200])

        except httpx.HTTPError as e:
            raise RuntimeError(f"ASI:One transport error: {e}") from e

    # Try to parse JSON regardless of status, so we can surface API errors.
    try:
        data = r.json()
    except ValueError as e:
        raise RuntimeError(
            f"ASI:One returned non-JSON body (status={r.status_code}): "
            f"{r.text[:300]!r}"
        ) from e

    if r.status_code >= 400 or "choices" not in data:
        # API-level error (auth, quota, rate limit, validation, ...)
        raise RuntimeError(
            f"ASI:One API error (status={r.status_code}): {data}"
        )

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"Unexpected ASI:One response shape: {data}"
        ) from e

    log.debug("[asi_one] raw reply: %s", text)
    verdict = _parse_agent_text(text)
    log.info("[asi_one] verdict=%s reason=%s",
             verdict["action"], verdict.get("reason", ""))
    
    ACTION_MAP = {
    "ALLOW":        ("LOW",    "KEEP_WIPER"),
    "STOP_WIPER":   ("HIGH",   "STOP_WIPER"),
    "REDUCE_SPEED": ("MEDIUM", "REDUCE_WIPER"),
    }

    action = verdict["action"]
    reason = verdict.get("reason", "")
    risk, rec = ACTION_MAP.get(action, ("HIGH", "STOP_WIPER"))

    return AsiOneVerdict(
        risk_level=risk,
        assessment=reason,
        recommended_action=rec,
    )
