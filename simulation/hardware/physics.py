import math


class GreasePhysicsModel:
    """
    Models grease flow behaviour as a function of temperature using an
    Arrhenius-like exponential viscosity model.

    Grease viscosity decreases exponentially with temperature (not linearly),
    which means flow rate increases exponentially and drip weight decreases
    exponentially. This is the key non-linearity that makes calibration at
    multiple temperatures necessary.

        viscosity(T) ∝ exp(-k * (T - T_ref))
        flow_rate(T) = base_flow_rate * exp(k * (T - T_ref))   [∝ 1/viscosity]
        drip_weight(T) = base_drip * exp(-k * (T - T_ref))     [∝ viscosity]

    With only linear interpolation in the controller (numpy.interp), this
    non-linearity produces real — but small — dispensing errors between
    calibration points, which is realistic.

    Defaults are representative values — tune them to match the real machine.
    """

    def __init__(
        self,
        base_flow_rate: float = 0.01,     # kg/s at reference temperature
        reference_temp: float = 20.0,     # °C
        viscosity_coeff: float = 0.015,   # Arrhenius exponent per °C
        base_drip: float = 0.05,          # kg drip at reference temperature
        base_drip_duration: float = 10.0, # seconds for drip to complete at reference temperature
    ) -> None:
        self.base_flow_rate = base_flow_rate
        self.reference_temp = reference_temp
        self.viscosity_coeff = viscosity_coeff
        self.base_drip = base_drip
        self.base_drip_duration = base_drip_duration

    def flow_rate(self, temperature: float) -> float:
        """kg/s — how fast grease exits while the motor is running."""
        delta = temperature - self.reference_temp
        return self.base_flow_rate * math.exp(self.viscosity_coeff * delta)

    def drip_weight(self, temperature: float) -> float:
        """kg — grease that keeps dripping after the motor stops."""
        delta = temperature - self.reference_temp
        return self.base_drip * math.exp(-self.viscosity_coeff * delta)

    def drip_duration(self, temperature: float) -> float:
        """
        Seconds for the full drip to complete after the motor stops.
        More viscous grease (lower temperature) drips more slowly.
        Uses the same exponential viscosity relationship.
        """
        delta = temperature - self.reference_temp
        return self.base_drip_duration * math.exp(-self.viscosity_coeff * delta)
