from __future__ import annotations

import time

from grease_machine.interfaces import IMotor, IScale, IThermometer
from grease_machine.calibration import CalibrationPoint, CalibrationStore, CALIBRATION_TARGET_KG


class CalibrationProcedure:
    """
    Runs the calibration procedure:
      1. Start motor, monitor scale until CALIBRATION_TARGET_KG is reached.
      2. Stop motor, record elapsed time.
      3. Wait for scale to stabilize (no change for stable_seconds).
      4. Record drip weight (final - target).
      5. Store and return the CalibrationPoint.

    Before running, ensure hoses are filled using ManualController.
    """

    POLL_INTERVAL = 0.1          # seconds between scale reads while motor is on
    STABLE_SECONDS = 30.0        # seconds of no change to consider weight stable
    STABLE_TOLERANCE = 0.001     # kg — changes smaller than this are considered noise
    STABILIZATION_TIMEOUT = 120  # seconds max to wait for stabilization

    def __init__(
        self,
        motor: IMotor,
        scale: IScale,
        thermometer: IThermometer,
        store: CalibrationStore,
    ) -> None:
        self._motor = motor
        self._scale = scale
        self._thermometer = thermometer
        self._store = store

    def run(self) -> CalibrationPoint:
        temperature = self._thermometer.read_temperature()

        # Dispense until scale reaches calibration target
        self._motor.start()
        start_time = time.monotonic()

        while True:
            weight = self._scale.read_weight()
            if weight >= CALIBRATION_TARGET_KG:
                self._motor.stop()
                motor_on_time = time.monotonic() - start_time
                break
            time.sleep(self.POLL_INTERVAL)

        # Wait for drip to finish (weight stable for STABLE_SECONDS)
        final_weight = self._wait_for_stabilization()
        drip_weight = final_weight - CALIBRATION_TARGET_KG

        point = CalibrationPoint(
            temperature=temperature,
            motor_on_time=motor_on_time,
            drip_weight=drip_weight,
        )
        self._store.add_point(point)
        return point

    def _wait_for_stabilization(self) -> float:
        """
        Poll the scale every second.
        Returns the final weight once it has not changed by more than
        STABLE_TOLERANCE kg for STABLE_SECONDS consecutive seconds.
        """
        stable_since = time.monotonic()
        last_weight = self._scale.read_weight()
        deadline = time.monotonic() + self.STABILIZATION_TIMEOUT

        while time.monotonic() < deadline:
            time.sleep(1.0)
            current_weight = self._scale.read_weight()

            if abs(current_weight - last_weight) > self.STABLE_TOLERANCE:
                last_weight = current_weight
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= self.STABLE_SECONDS:
                return current_weight

        return self._scale.read_weight()
