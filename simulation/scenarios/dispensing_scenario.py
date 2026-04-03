"""
Scenario 2 — Dispensing accuracy at various target weights.

Loads the calibration store produced by calibration_scenario.py,
then for each target weight:
  1. Computes motor_on_time via interpolation at the current temperature.
  2. Simulates the motor running for that time.
  3. Computes the actual dispensed weight (motor flow + drip).
  4. Reports the error.

Run calibration_scenario.py first to generate calibration_data.json.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import matplotlib.pyplot as plt

from grease_machine.calibration import CalibrationStore, Interpolator
from simulation.hardware.physics import GreasePhysicsModel


def simulate_dispense(
    physics: GreasePhysicsModel,
    motor_on_time: float,
    temperature: float,
) -> float:
    """Return the actual weight dispensed given motor on-time."""
    flow = physics.flow_rate(temperature)
    drip = physics.drip_weight(temperature)
    return motor_on_time * flow + drip


def run() -> None:
    store_path = os.path.join(os.path.dirname(__file__), "..", "calibration_data.json")
    if not os.path.exists(store_path):
        print("ERROR: calibration_data.json not found. Run calibration_scenario.py first.")
        return

    store = CalibrationStore.load(store_path)
    interpolator = Interpolator(store)
    physics = GreasePhysicsModel()

    temperature = 25.0  # °C — between calibration points, to show interpolation
    target_weights = [0.5, 1.0, 2.0, 5.0, 8.0]

    print("=== Dispensing Accuracy Scenario ===\n")
    print(f"Temperature: {temperature}°C\n")
    print(f"{'Target (kg)':>12} {'Motor time (s)':>15} {'Actual (kg)':>12} {'Error (g)':>10} {'Error %':>8}")
    print("-" * 61)

    targets, actuals, errors_g = [], [], []
    for target in target_weights:
        motor_time = interpolator.get_motor_time(target, temperature)
        actual = simulate_dispense(physics, motor_time, temperature)
        error_g = (actual - target) * 1000
        error_pct = (actual - target) / target * 100

        targets.append(target)
        actuals.append(actual)
        errors_g.append(error_g)

        print(f"{target:>12.2f} {motor_time:>15.4f} {actual:>12.4f} {error_g:>+10.2f} {error_pct:>+8.3f}%")

    print()

    errors_pct = [(a - t) / t * 100 for a, t in zip(actuals, targets)]
    TOLERANCE_G = 10.0  # acceptable error band in grams

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Dispensing Accuracy at {temperature}°C", fontsize=13)

    # Left: target vs actual with residual zoom
    axes[0].plot(targets, targets, "--", color="grey", linewidth=1, label="Ideal")
    axes[0].plot(targets, actuals, "o-", color="steelblue", linewidth=2, label="Actual")
    for t, a in zip(targets, actuals):
        axes[0].annotate(
            f"{(a - t) * 1000:+.1f} g",
            xy=(t, a),
            xytext=(6, -14),
            textcoords="offset points",
            fontsize=8,
            color="crimson",
        )
    axes[0].set_xlabel("Target weight (kg)")
    axes[0].set_ylabel("Dispensed weight (kg)")
    axes[0].set_title("Target vs Actual")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Right: lollipop error chart with tolerance band
    ax = axes[1]
    ax.axhspan(-TOLERANCE_G, TOLERANCE_G, color="lightgreen", alpha=0.25, label=f"±{TOLERANCE_G:.0f} g tolerance")
    ax.axhline(0, color="black", linewidth=0.9)

    for t, e, ep in zip(targets, errors_g, errors_pct):
        color = "steelblue" if abs(e) <= TOLERANCE_G else "crimson"
        ax.vlines(t, 0, e, colors=color, linewidth=2)
        ax.plot(t, e, "o", color=color, markersize=9, zorder=5)
        ax.annotate(
            f"{e:+.1f} g\n({ep:+.2f}%)",
            xy=(t, e),
            xytext=(0, -26 if e < 0 else 8),
            textcoords="offset points",
            ha="center",
            fontsize=7.5,
            color=color,
        )

    ax.set_xlabel("Target weight (kg)")
    ax.set_ylabel("Error (g)")
    ax.set_title("Interpolation Error (linear interp over exponential physics)")
    ax.set_xticks(targets)
    ax.set_xticklabels([f"{t} kg" for t in targets])
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(True, alpha=0.25, axis="y")
    ax.margins(x=0.15)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "..", "dispensing_accuracy.png"), dpi=120)
    plt.show()


if __name__ == "__main__":
    run()
