"""Client-side mirror of the deployed agent's message models.

These MUST match the field names in the hosted smartwiper-safety agent:
    WiperSafetyRequest(hood_is_open, current_wiper_mode, vehicle_speed)
    WiperSafetyResponse(risk_level, assessment, recommended_action)
"""
from dataclasses import dataclass
from typing import Literal

from uagents import Model


WiperMode = Literal["OFF", "SLOW", "MEDIUM", "FAST"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Action = Literal["STOP_WIPER", "KEEP_WIPER", "REDUCE_WIPER"]


# --- uAgents wire models (Path A) -------------------------------------
class WiperSafetyRequest(Model):
    hood_is_open: bool
    current_wiper_mode: str
    vehicle_speed: float


class WiperSafetyResponse(Model):
    risk_level: str
    assessment: str
    recommended_action: str


# --- Bridge-internal normalized verdict (returned to Velocitas) -------
@dataclass(frozen=True)
class SafetyVerdict:
    risk_level: str          # LOW | MEDIUM | HIGH
    assessment: str
    recommended_action: str  # STOP_WIPER | KEEP_WIPER | REDUCE_WIPER

    @classmethod
    def from_response(cls, r: WiperSafetyResponse) -> "SafetyVerdict":
        return cls(
            risk_level=r.risk_level,
            assessment=r.assessment,
            recommended_action=r.recommended_action,
        )
