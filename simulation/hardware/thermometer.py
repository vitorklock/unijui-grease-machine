class SimulatedThermometer:
    """
    Simulated thermometer that returns a fixed temperature.
    Implements grease_machine.interfaces.IThermometer.
    """

    def __init__(self, temperature: float = 20.0) -> None:
        self.temperature = temperature

    def read_temperature(self) -> float:
        return self.temperature
