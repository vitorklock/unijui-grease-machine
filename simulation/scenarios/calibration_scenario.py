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
    print(f"{'Temp (°C)':>10} {'Flow rate (kg/s)':>18} {'Motor time (s)':>15} {'Drip (kg)':>10} {'Drip time (s)':>14}")
    print("-" * 71)

    for temp in calibration_temperatures:
        point = simulate_calibration(physics, temp)
        store.add_point(point)
        drip_t = physics.drip_duration(temp)
        print(f"{temp:>10.1f} {point.flow_rate:>18.4f} {point.motor_on_time:>15.4f} {point.drip_weight:>10.4f} {drip_t:>14.2f}")

    print()

    # Save calibration store
    store_path = os.path.join(os.path.dirname(__file__), "..", "calibration_data.json")
    store.save(store_path)
    print(f"Calibration saved to: {os.path.abspath(store_path)}\n")

    # Dense temperature range for smooth curves
    import numpy as np
    temp_range = np.linspace(calibration_temperatures[0], calibration_temperatures[-1], 200)

    temps = [p.temperature for p in store.points]
    flow_rates = [p.flow_rate for p in store.points]
    drip_weights = [p.drip_weight for p in store.points]
    motor_times = [p.motor_on_time for p in store.points]
    drip_durations = [physics.drip_duration(t) for t in temps]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Calibration Curves", fontsize=14)

    # Flow rate
    axes[0, 0].plot(temp_range, [physics.flow_rate(t) for t in temp_range], color="steelblue", alpha=0.4)
    axes[0, 0].plot(temps, flow_rates, "o", color="steelblue", markersize=8, label="Calibration points")
    axes[0, 0].set_xlabel("Temperature (°C)")
    axes[0, 0].set_ylabel("Flow rate (kg/s)")
    axes[0, 0].set_title("Flow Rate vs Temperature")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, alpha=0.3)

    # Drip weight
    axes[0, 1].plot(temp_range, [physics.drip_weight(t) for t in temp_range], color="darkorange", alpha=0.4)
    axes[0, 1].plot(temps, drip_weights, "o", color="darkorange", markersize=8, label="Calibration points")
    axes[0, 1].set_xlabel("Temperature (°C)")
    axes[0, 1].set_ylabel("Drip weight (kg)")
    axes[0, 1].set_title("Drip Weight vs Temperature")
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, alpha=0.3)

    # Motor on-time
    axes[1, 0].plot(temp_range, [CALIBRATION_TARGET_KG / physics.flow_rate(t) for t in temp_range], color="seagreen", alpha=0.4)
    axes[1, 0].plot(temps, motor_times, "o", color="seagreen", markersize=8, label="Calibration points")
    axes[1, 0].set_xlabel("Temperature (°C)")
    axes[1, 0].set_ylabel("Motor on-time (s)")
    axes[1, 0].set_title(f"Motor Time for {CALIBRATION_TARGET_KG} kg vs Temperature")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, alpha=0.3)

    # Drip duration — how long to wait after motor stops
    ax = axes[1, 1]
    drip_dur_range = [physics.drip_duration(t) for t in temp_range]
    ax.fill_between(temp_range, drip_dur_range, alpha=0.15, color="mediumpurple")
    ax.plot(temp_range, drip_dur_range, color="mediumpurple", alpha=0.6)
    ax.plot(temps, drip_durations, "o", color="mediumpurple", markersize=8, label="Calibration points")
    for t, d in zip(temps, drip_durations):
        ax.annotate(
            f"{d:.1f} s",
            xy=(t, d),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=8,
            color="mediumpurple",
        )
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Drip duration (s)")
    ax.set_title("Drip Duration vs Temperature\n(wait time after motor stops)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "..", "calibration_curves.png"), dpi=120)
    plt.show()

    return store


if __name__ == "__main__":
    run()
