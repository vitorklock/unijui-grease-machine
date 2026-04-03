import time


class SimulatedMotor:
    """
    Simulated motor that tracks running state and elapsed on-time.
    Implements grease_machine.interfaces.IMotor.
    """

    def __init__(self) -> None:
        self._running = False
        self._start_time: float | None = None
        self._total_on_time: float = 0.0

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._start_time = time.monotonic()

    def stop(self) -> None:
        if self._running:
            assert self._start_time is not None
            self._total_on_time += time.monotonic() - self._start_time
            self._running = False
            self._start_time = None

    def is_running(self) -> bool:
        return self._running

    def get_elapsed_on_time(self) -> float:
        """Total seconds the motor has been running (including current session)."""
        if self._running and self._start_time is not None:
            return self._total_on_time + (time.monotonic() - self._start_time)
        return self._total_on_time

    def reset(self) -> None:
        """Reset accumulated on-time (call between dispensing operations)."""
        self.stop()
        self._total_on_time = 0.0
