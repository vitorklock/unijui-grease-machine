import time

from .motor import SimulatedMotor
from .physics import GreasePhysicsModel
from .thermometer import SimulatedThermometer

DRIP_DURATION = 10.0   # seconds over which drip accumulates after motor stops


class SimulatedScale:
    """
    Simulated scale that computes weight from physics model.
    Implements grease_machine.interfaces.IScale.

    Weight while motor is on:
        weight = elapsed_on_time * flow_rate(T)

    After motor stops, drip accumulates linearly over DRIP_DURATION seconds:
        weight += drip_fraction * drip_weight(T)
    """

    def __init__(
        self,
        motor: SimulatedMotor,
        physics: GreasePhysicsModel,
        thermometer: SimulatedThermometer,
    ) -> None:
        self._motor = motor
        self._physics = physics
        self._thermometer = thermometer

        self._stop_time: float | None = None
        self._weight_at_stop: float = 0.0
        self._was_running: bool = False

    def read_weight(self) -> float:
        temperature = self._thermometer.read_temperature()
        flow_rate = self._physics.flow_rate(temperature)
        drip_weight = self._physics.drip_weight(temperature)

        running = self._motor.is_running()

        # Detect motor stop transition
        if self._was_running and not running:
            self._stop_time = time.monotonic()
            self._weight_at_stop = self._motor.get_elapsed_on_time() * flow_rate
        self._was_running = running

        if running:
            return self._motor.get_elapsed_on_time() * flow_rate

        # Motor is stopped — add drip fraction
        base_weight = self._weight_at_stop
        if self._stop_time is not None:
            elapsed_since_stop = time.monotonic() - self._stop_time
            drip_fraction = min(1.0, elapsed_since_stop / DRIP_DURATION)
            return base_weight + drip_fraction * drip_weight

        return base_weight

    def reset(self) -> None:
        """Reset scale state between operations."""
        self._stop_time = None
        self._weight_at_stop = 0.0
        self._was_running = False
