"""
Scenario 3 — Manual controller vs Automatic controller.

Simulates a human operator trying to dispense exactly 1.0 kg manually
(by watching the weight and guessing when to stop) vs the AutomaticController
that uses interpolation.

The "human" is modelled as stopping the motor with some reaction delay and error.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import random
import matplotlib.pyplot as plt
import numpy as np

from grease_machine.calibration import CalibrationStore, Interpolator
from simulation.hardware.physics import GreasePhysicsModel

TARGET_WEIGHT = 1.0    # kg
TEMPERATURE = 25.0     # °C
N_TRIALS = 20          # how many times each "operator" tries


def simulate_auto(physics: GreasePhysicsModel, store: CalibrationStore) -> float:
    """Automatic controller: compute exact motor time, return actual weight."""
    motor_time = Interpolator(store).get_motor_time(TARGET_WEIGHT, TEMPERATURE)
    actual = motor_time * physics.flow_rate(TEMPERATURE) + physics.drip_weight(TEMPERATURE)
    return actual


def simulate_manual(physics: GreasePhysicsModel, seed: int) -> float:
    """
    Human operator: tries to stop when the scale reads TARGET_WEIGHT - drip.
    Models reaction delay (0.1–0.5 s) and reading error (±5 g).
    """
    rng = random.Random(seed)

    drip = physics.drip_weight(TEMPERATURE)
    flow = physics.flow_rate(TEMPERATURE)

    # Human aims to stop at (target - drip), but has reaction delay and reading error
    reaction_delay = rng.uniform(0.1, 0.5)   # seconds late
    reading_error = rng.gauss(0, 0.005)       # ±5 g std dev

    # Weight at which they decide to stop (intended stop point)
    intended_stop_weight = TARGET_WEIGHT - drip + reading_error
    # Time to reach that weight
    time_to_intended = intended_stop_weight / flow
    # Actual stop time (delayed by reaction)
    actual_stop_time = time_to_intended + reaction_delay
    # Actual weight dispensed
    actual = actual_stop_time * flow + drip
    return actual


def run() -> None:
    store_path = os.path.join(os.path.dirname(__file__), "..", "calibration_data.json")
    if not os.path.exists(store_path):
        print("ERROR: calibration_data.json not found. Run calibration_scenario.py first.")
        return

    store = CalibrationStore.load(store_path)
    physics = GreasePhysicsModel()

    auto_results = [simulate_auto(physics, store) for _ in range(N_TRIALS)]
    manual_results = [simulate_manual(physics, seed=i) for i in range(N_TRIALS)]

    auto_errors_g = [(w - TARGET_WEIGHT) * 1000 for w in auto_results]
    manual_errors_g = [(w - TARGET_WEIGHT) * 1000 for w in manual_results]

    print("=== Manual vs Automatic Controller Scenario ===\n")
    print(f"Target weight: {TARGET_WEIGHT} kg at {TEMPERATURE}°C, {N_TRIALS} trials\n")

    print(f"{'':>25} {'Auto':>10} {'Manual':>10}")
    print("-" * 47)
    print(f"{'Mean error (g)':>25} {np.mean(auto_errors_g):>+10.2f} {np.mean(manual_errors_g):>+10.2f}")
    print(f"{'Std dev (g)':>25} {np.std(auto_errors_g):>10.2f} {np.std(manual_errors_g):>10.2f}")
    print(f"{'Max over-dispense (g)':>25} {max(auto_errors_g):>+10.2f} {max(manual_errors_g):>+10.2f}")
    print(f"{'Max under-dispense (g)':>25} {min(auto_errors_g):>+10.2f} {min(manual_errors_g):>+10.2f}")
    print()

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(f"Manual vs Automatic: dispensing {TARGET_WEIGHT} kg at {TEMPERATURE}°C", fontsize=13)

    trial_idx = list(range(1, N_TRIALS + 1))
    axes[0].plot(trial_idx, auto_errors_g, "o-", color="steelblue", label="Automatic")
    axes[0].plot(trial_idx, manual_errors_g, "s--", color="darkorange", label="Manual (human)")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_xlabel("Trial")
    axes[0].set_ylabel("Error (g)")
    axes[0].set_title("Error per Trial")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(auto_errors_g, bins=8, alpha=0.7, color="steelblue", label="Automatic")
    axes[1].hist(manual_errors_g, bins=8, alpha=0.7, color="darkorange", label="Manual")
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].set_xlabel("Error (g)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Error Distribution")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "..", "manual_vs_auto.png"), dpi=120)
    plt.show()


if __name__ == "__main__":
    run()
