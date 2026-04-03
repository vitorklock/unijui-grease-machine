from grease_machine.interfaces import IMotor


class ManualController:
    """
    Direct motor control — the operator is in charge.

    Use this for filling hoses (hold motor_on until full, then motor_off)
    and for human-skill comparisons in simulation.
    """

    def __init__(self, motor: IMotor) -> None:
        self._motor = motor

    def motor_on(self) -> None:
        """Start the motor. Equivalent to pressing and holding the fill button."""
        self._motor.start()

    def motor_off(self) -> None:
        """Stop the motor. Equivalent to releasing the fill button."""
        self._motor.stop()

    def is_running(self) -> bool:
        return self._motor.is_running()
