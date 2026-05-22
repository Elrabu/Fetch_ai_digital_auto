"""SmartWiper Velocitas vehicle app."""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import sys

from velocitas_sdk.vehicle_app import VehicleApp, subscribe_data_points
from velocitas_sdk.vdb.subscriptions import DataPointReply
from vehicle import Vehicle, vehicle
from bridge.safety_bridge import evaluate_safety

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SmartWiper")


class SmartWiperApp(VehicleApp):
    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        log.info("SmartWiperApp starting.")
        # Kick off a one-shot evaluation using current VSS values.
        asyncio.create_task(self._run_once())

    async def _run_once(self):
        hood_is_open = bool((await self.Vehicle.Body.Hood.IsOpen.get()).value)
        current_wiper_mode = str(
            (await self.Vehicle.Body.Windshield.Front.Wiping.Mode.get()).value
        )
        vehicle_speed = float((await self.Vehicle.Speed.get()).value)
        await self._evaluate_and_halt(hood_is_open, current_wiper_mode, vehicle_speed)

    @subscribe_data_points(
        "Vehicle.Body.Hood.IsOpen,"
        "Vehicle.Body.Windshield.Front.Wiping.Mode,"
        "Vehicle.Speed"
    )
    async def on_vss_change(self, data: DataPointReply):
        hood_is_open = bool(data.get(self.Vehicle.Body.Hood.IsOpen).value)
        current_wiper_mode = str(
            data.get(self.Vehicle.Body.Windshield.Front.Wiping.Mode).value
        )
        vehicle_speed = float(data.get(self.Vehicle.Speed).value)
        await self._evaluate_and_halt(hood_is_open, current_wiper_mode, vehicle_speed)

    async def _evaluate_and_halt(self, hood_is_open, current_wiper_mode, vehicle_speed):
        try:
            verdict = await evaluate_safety(
                hood_is_open=hood_is_open,
                current_wiper_mode=current_wiper_mode,
                vehicle_speed=vehicle_speed,
            )
        except Exception as e:
            log.exception(f"Safety evaluation failed; failing safe (STOP_WIPER): {e}")
            await self._actuate_stop()
            self._demo_halt("STOP_WIPER", "ERROR", str(e))
            return

        log.info(
            f"Verdict: risk={verdict.risk_level} "
            f"action={verdict.recommended_action} -- {verdict.assessment}"
        )

        if verdict.recommended_action == "STOP_WIPER":
            await self._actuate_stop()
        elif verdict.recommended_action == "REDUCE_WIPER":
            await self._actuate_reduce(current_wiper_mode)

        self._demo_halt(
            verdict.recommended_action,
            verdict.risk_level,
            verdict.assessment,
        )

    async def _actuate_stop(self):
        await self.Vehicle.Body.Windshield.Front.Wiping.Mode.set("OFF")

    async def _actuate_reduce(self, current_mode: str):
        downshift = {"FAST": "MEDIUM", "MEDIUM": "SLOW", "SLOW": "OFF", "OFF": "OFF"}
        target = downshift.get(current_mode.upper(), "OFF")
        await self.Vehicle.Body.Windshield.Front.Wiping.Mode.set(target)

    def _demo_halt(self, action: str, risk: str, reason: str):
        print("\n" + "=" * 60)
        print(f" SAFETY ACTION TAKEN: {action}")
        print(f"   Risk level: {risk}")
        print(f"   Reasoning:  {reason}")
        print("=" * 60 + "\n", flush=True)
        sys.exit(0)


async def main():
    app = SmartWiperApp(vehicle)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
