from __future__ import annotations

import time
from dataclasses import dataclass

from grease_machine.interfaces import IMotor, IThermometer
from grease_machine.calibration import CalibrationStore, Interpolator


@dataclass
class DispenseResult:
    target_weight: float    # kg requested
    temperature: float      # °C at time of dispensing
    motor_on_time: float    # seconds the motor ran


class AutomaticController:
    """
    Automatic grease dispenser.

    Reads the current temperature, looks up the required motor-on time via
    interpolation over the calibration store, runs the motor for exactly that
    duration, then stops.

    Prerequisites:
    - The calibration store must have at least 2 CalibrationPoints.
    - The hoses must already be filled (use ManualController.motor_on/off for that).
    """

    def __init__(
        self,
        motor: IMotor,
        thermometer: IThermometer,
        store: CalibrationStore,
    ) -> None:
        self._motor = motor
        self._thermometer = thermometer
        self._store = store

    def dispense(self, target_weight: float) -> DispenseResult:
        """
        Dispense exactly target_weight kg of grease.

        Raises:
            InsufficientCalibrationError: if the store has fewer than 2 points.
            ValueError: if target_weight is not achievable with current calibration.
        """
        temperature = self._thermometer.read_temperature()
        motor_on_time = Interpolator(self._store).get_motor_time(target_weight, temperature)

        self._motor.start()
        time.sleep(motor_on_time)
        self._motor.stop()

        return DispenseResult(
            target_weight=target_weight,
            temperature=temperature,
            motor_on_time=motor_on_time,
        )
