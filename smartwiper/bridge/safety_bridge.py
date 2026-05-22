"""Bridge between the Velocitas vehicle app and the deployed
smartwiper-safety agent.

Path A (default):  typed uAgents query → hosted agent
Path B (USE_ASI_ONE=1): ASI:One agentic completion → hosted agent (NL)

Both paths return the same SafetyVerdict dataclass.
"""
import logging
import os

from uagents.query import query
from pathlib import Path
from dotenv import load_dotenv
from bridge.asi_one_client import ask_via_asi_one

from bridge.models import (
    WiperSafetyRequest,
    WiperSafetyResponse,
    SafetyVerdict,
)
from bridge.asi_one_client import ask_via_asi_one

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

log = logging.getLogger("safety_bridge")

SAFETY_AGENT_ADDRESS = os.environ.get("SAFETY_AGENT_ADDRESS", "")
USE_ASI_ONE = os.environ.get("USE_ASI_ONE", "0") == "1"


async def _path_a_typed(
    hood_is_open: bool, current_wiper_mode: str, vehicle_speed: float
) -> WiperSafetyResponse:
    if not SAFETY_AGENT_ADDRESS:
        raise RuntimeError(
            "SAFETY_AGENT_ADDRESS not set; required for typed path."
        )
    req = WiperSafetyRequest(
        hood_is_open=hood_is_open,
        current_wiper_mode=current_wiper_mode,
        vehicle_speed=vehicle_speed,
    )
    envelope = await query(
        destination=SAFETY_AGENT_ADDRESS, message=req, timeout=10.0
    )
    return WiperSafetyResponse.model_validate_json(envelope.decode_payload())


async def _path_b_asi_one(
    hood_is_open: bool, current_wiper_mode: str, vehicle_speed: float
) -> WiperSafetyResponse:
    return await ask_via_asi_one(hood_is_open, current_wiper_mode, vehicle_speed)

async def evaluate_safety(*, hood_is_open: bool, current_wiper_mode: str, vehicle_speed: float):
    log.info("[bridge] route=ASI:One")
    return await ask_via_asi_one(
        hood_is_open=hood_is_open,
        current_wiper_mode=current_wiper_mode,
        vehicle_speed=vehicle_speed,
    )