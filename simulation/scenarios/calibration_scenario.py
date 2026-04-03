"""
Scenario 1 — Calibration at multiple temperatures.

Runs the calibration procedure (simulated, no real sleeping) at three temperatures
and plots the resulting calibration curve.

The simulation computes how long the motor needs to run to reach 5 kg at each
temperature, records the drip, and builds the CalibrationStore.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import matplotlib.pyplot as plt

from grease_machine.calibration import CalibrationPoint, CalibrationStore, CALIBRATION_TARGET_KG
from simulation.hardware.physics import GreasePhysicsModel


def simulate_calibration(physics: GreasePhysicsModel, temperature: float) -> CalibrationPoint:
    """
    Analytically compute the calibration result for a given temperature.
    This is the fast (non-sleeping) equivalent of CalibrationProcedure.run().
    """
    flow_rate = physics.flow_rate(temperature)
    drip_weight = physics.drip_weight(temperature)

    # How long until the scale reads exactly CALIBRATION_TARGET_KG?
    # weight(t) = t * flow_rate  →  t = target / flow_rate
    motor_on_time = CALIBRATION_TARGET_KG / flow_rate

    return CalibrationPoint(
        temperature=temperature,
        motor_on_time=motor_on_time,
        drip_weight=drip_weight,
    )


def run() -> CalibrationStore:
    physics = GreasePhysicsModel()
    store = CalibrationStore()

    calibration_temperatures = [10.0, 20.0, 35.0]

    print("=== Calibration Scenario ===\n")
    print(f"{'Temp (°C)':>10} {'Flow rate (kg/s)':>18} {'Motor time (s)':>15} {'Drip (kg)':>10}")
    print("-" * 57)

    for temp in calibration_temperatures:
        point = simulate_calibration(physics, temp)
        store.add_point(point)
        print(f"{temp:>10.1f} {point.flow_rate:>18.4f} {point.motor_on_time:>15.4f} {point.drip_weight:>10.4f}")

    print()

    # Save calibration store
    store_path = os.path.join(os.path.dirname(__file__), "..", "calibration_data.json")
    store.save(store_path)
    print(f"Calibration saved to: {os.path.abspath(store_path)}\n")

    # Plot
    temps = [p.temperature for p in store.points]
    flow_rates = [p.flow_rate for p in store.points]
    drip_weights = [p.drip_weight for p in store.points]
    motor_times = [p.motor_on_time for p in store.points]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle("Calibration Curves", fontsize=13)

    axes[0].plot(temps, flow_rates, "o-", color="steelblue")
    axes[0].set_xlabel("Temperature (°C)")
    axes[0].set_ylabel("Flow rate (kg/s)")
    axes[0].set_title("Flow Rate vs Temperature")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(temps, drip_weights, "o-", color="darkorange")
    axes[1].set_xlabel("Temperature (°C)")
    axes[1].set_ylabel("Drip weight (kg)")
    axes[1].set_title("Drip Weight vs Temperature")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(temps, motor_times, "o-", color="seagreen")
    axes[2].set_xlabel("Temperature (°C)")
    axes[2].set_ylabel("Motor on-time (s)")
    axes[2].set_title(f"Motor Time for {CALIBRATION_TARGET_KG} kg vs Temperature")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "..", "calibration_curves.png"), dpi=120)
    plt.show()

    return store


if __name__ == "__main__":
    run()
