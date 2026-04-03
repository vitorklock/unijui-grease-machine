from typing import Protocol, runtime_checkable


@runtime_checkable
class IMotor(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...


@runtime_checkable
class IScale(Protocol):
    def read_weight(self) -> float: ...
    """Returns current weight in kg."""


@runtime_checkable
class IThermometer(Protocol):
    def read_temperature(self) -> float: ...
    """Returns current temperature in Celsius."""
