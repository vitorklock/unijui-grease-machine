from __future__ import annotations

import numpy as np

from .data import CalibrationStore


class InsufficientCalibrationError(Exception):
    """Raised when the store has fewer than 2 calibration points."""


class Interpolator:
    def __init__(self, store: CalibrationStore) -> None:
        self._store = store

    def get_motor_time(self, target_weight: float, temperature: float) -> float:
        """
        Compute motor-on time (seconds) to dispense target_weight kg at the given temperature.

        Uses numpy.interp over the calibration points to estimate flow_rate and drip_weight
        at the current temperature, then solves:
            motor_time = (target_weight - drip_weight_at_T) / flow_rate_at_T
        """
        points = self._store.points
        if len(points) < 2:
            raise InsufficientCalibrationError(
                f"Need at least 2 calibration points, have {len(points)}."
            )

        temps = np.array([p.temperature for p in points])
        flow_rates = np.array([p.flow_rate for p in points])
        drip_weights = np.array([p.drip_weight for p in points])

        flow_rate_at_T = float(np.interp(temperature, temps, flow_rates))
        drip_at_T = float(np.interp(temperature, temps, drip_weights))

        dispensed_while_running = target_weight - drip_at_T
        if dispensed_while_running <= 0:
            raise ValueError(
                f"Target weight {target_weight} kg is less than or equal to drip weight "
                f"{drip_at_T:.3f} kg at {temperature}°C. Cannot compute motor time."
            )

        return dispensed_while_running / flow_rate_at_T
