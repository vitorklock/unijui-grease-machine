# Grease Machine — System Documentation

## Overview

The Grease Machine is a grease dispensing system that uses a motor-driven pump to fill parts with a precise amount of grease. Two taps split the output between both sides of the part being filled.

The system's core objective is **precision**: given a target weight (e.g. 1 kg of grease), the system determines exactly how long to run the motor so that the correct amount is dispensed — accounting for the fact that grease continues to flow after the motor stops, and that the grease's behavior changes with temperature.

The project is split into two independent parts:

1. **Control software** (`grease_machine/`) — the real controller logic, hardware interfaces, calibration engine, and automatic dispenser. This is a standalone Python package that can be used with real hardware in the future.
2. **Simulation** (`simulation/`) — a physics-based simulation of grease flow that lets us test, demonstrate, and validate the control software without a physical machine.

---

## How the System Works

### The Problem

Grease does not stop flowing the instant the motor turns off. Some amount of grease remains in the hoses and taps and continues to drip into the container by gravity. This "drip" means that if the motor runs long enough to pump exactly 1 kg, the final weight will always be *more* than 1 kg.

Additionally, grease viscosity changes with temperature:
- **Colder grease** is thicker — it flows more slowly while the motor is on, but also clings more to the hoses, resulting in heavier and longer drip after the motor stops.
- **Warmer grease** is thinner — it flows faster, but less remains in the hoses, so drip is lighter and faster.

This means there is no single "correct" motor runtime for a given weight. The correct runtime depends on the current temperature.

### The Solution

The system uses a **calibration-then-dispense** approach:

1. **Calibrate** the system at multiple temperatures to learn how the grease behaves.
2. **Interpolate** between calibration points to compute the correct motor runtime for any target weight at any temperature.
3. **Dispense** by running the motor for exactly the computed duration, then stopping.

The formula used is:

```
motor_on_time = (target_weight - drip_weight_at_current_temp) / flow_rate_at_current_temp
```

This accounts for the drip: since `drip_weight` grams will flow after the motor stops, the motor only needs to pump `target_weight - drip_weight` grams while running.

---

## Calibration

### Why Calibration is Necessary

Every physical setup is different. The flow rate and drip behavior depend on:
- The motor and its pump capacity
- The hose diameter, length, and routing
- The tap configuration
- The grease brand and its specific viscosity curve

Rather than trying to model all of these variables, the system measures them directly through calibration. This makes the system adaptable to any hardware configuration.

### Calibration Procedure

Each calibration run works as follows:

1. The operator fills the hoses manually (using the **manual control mode** — holding the motor on until grease exits the taps, ensuring there is no air in the lines).
2. A container is placed on the scale and the scale is zeroed.
3. The system starts the motor and monitors the scale in real time.
4. When the scale reads **5 kg** (the calibration target), the motor stops and the elapsed time is recorded.
5. The system then waits for the weight to **stabilize** — it monitors the scale every second and considers the weight stable when it has not changed by more than 1 gram for **30 consecutive seconds**. This accounts for the full drip, which can take longer than expected with cold, viscous grease.
6. The final weight is recorded. The difference between the final weight and the 5 kg target is the **drip weight** at this temperature.

From a single calibration, the system derives:
- **Flow rate** (kg/s) = 5.0 / motor_on_time
- **Drip weight** (kg) = final_weight - 5.0

### Minimum Two Calibrations Required

The system requires **at least two calibration points at different temperatures** to operate. This is because:
- With a single point, the system only knows how the grease behaves at that exact temperature. It cannot predict behavior at any other temperature.
- With two or more points, the system can **interpolate** between them to estimate flow rate and drip weight at any temperature within the calibrated range.

The more calibration points collected at different temperatures, the more accurate the interpolation becomes — especially because grease viscosity follows a non-linear (exponential) relationship with temperature. Linear interpolation between widely spaced calibration points will introduce small errors. Adding calibration points in between reduces this error.

**Recommendation**: calibrate on the coldest and warmest days the machine will operate in, plus at least one intermediate temperature.

### Calibration Data Storage

Calibration data is stored as a JSON file with one entry per calibration:

```json
[
  {
    "temperature": 10.0,
    "motor_on_time": 11.62,
    "drip_weight": 0.1743
  },
  {
    "temperature": 20.0,
    "motor_on_time": 10.00,
    "drip_weight": 0.1500
  },
  {
    "temperature": 35.0,
    "motor_on_time": 7.99,
    "drip_weight": 0.1198
  }
]
```

This file is portable and human-readable. The system can load it on startup and use it immediately.

### When to Recalibrate

All existing calibration data must be cleared and the system recalibrated from scratch whenever the physical setup changes:

- **Motor replaced or adjusted** — different pump capacity changes the flow rate.
- **Hoses changed** — different diameter, length, or routing changes both flow rate and drip behavior (the volume of grease that remains in the hose after the motor stops).
- **Taps replaced or reconfigured** — affects how the flow is split and how much remains in the tap bodies.
- **Different grease brand** — different formulation means different viscosity curve. Even two greases rated at the same NLGI grade can behave differently at the same temperature.

Recalibration is simple: clear the calibration store and repeat the procedure at multiple temperatures.

---

## Operating Modes

### Manual Control

The manual controller provides direct motor control:
- **Motor on**: the operator presses and holds a button. The motor runs as long as the button is held.
- **Motor off**: the operator releases the button. The motor stops.

This mode is used for:
- **Filling hoses** before the first calibration or after hardware changes. The hoses must be completely filled with grease (no air pockets) before calibration or dispensing can begin.
- **Purging air** after long periods of inactivity.
- **Operator-controlled dispensing** when the automatic system is not calibrated or not appropriate.

The manual controller has **no dependency on calibration data**. It works with just a motor. No scale or thermometer is needed.

### Automatic Dispensing

The automatic controller handles the entire dispensing process:

1. Reads the current temperature from the thermometer.
2. Looks up the calibration data and interpolates to find the correct flow rate and drip weight at the current temperature.
3. Computes exactly how long the motor needs to run: `(target_weight - drip) / flow_rate`.
4. Starts the motor, waits for the computed duration, then stops the motor.

The result is a precise dispense that accounts for both the temperature-dependent flow rate and the temperature-dependent drip. The operator only needs to specify the target weight.

**The scale is not needed during normal operation.** It is only used during calibration. Once calibrated, the system operates purely on time — it knows how long to run the motor and trusts that the flow behavior matches the calibration data.

---

## Temperature Compensation

Temperature is a first-class concern in this system. Grease viscosity follows an exponential relationship with temperature (Arrhenius-like behavior):

- **Flow rate** increases exponentially with temperature (thinner grease flows faster).
- **Drip weight** decreases exponentially with temperature (thinner grease clings less).
- **Drip duration** decreases exponentially with temperature (thinner grease drips faster).

This means that at 10°C, the motor might need to run for ~12 seconds to dispense 5 kg, while at 35°C it might only need ~8 seconds. The drip at 10°C might be 174 g, while at 35°C it drops to 120 g. Running with the wrong timing — ignoring temperature — can cause errors of hundreds of grams.

The system reads the temperature at the moment of dispensing and adjusts accordingly. There is no need for the operator to manually adjust settings for different weather conditions.

---

## Hardware Requirements

### For Calibration
- **Motor** (with on/off control)
- **Scale** (reads weight in kg, accurate to at least 1 g)
- **Thermometer** (reads ambient/grease temperature in °C)

### For Normal Operation
- **Motor** (with on/off control)
- **Thermometer** (reads ambient/grease temperature in °C)

### For Manual Mode (hose filling, purging)
- **Motor** (with on/off control)

The scale is deliberately **not required** during normal dispensing. This simplifies the operational setup — the scale can be stored away after calibration and only brought out when recalibration is needed.

---

## Software Architecture

### Hardware Abstraction

The control software communicates with hardware through three interfaces (protocols):
- `IMotor` — start, stop, check if running
- `IScale` — read weight
- `IThermometer` — read temperature

Any device that implements these methods can be used with the system. This means:
- The same control code works with the simulation and with real hardware.
- Different motors, scales, or thermometers can be swapped in without changing the controller logic.
- Future integrations (e.g., Raspberry Pi GPIO, serial sensors, industrial PLCs) only need to implement these three simple interfaces.

### Independence from Simulation

The control software (`grease_machine/`) has **no dependency** on the simulation. It is a standalone package that can be used directly with real hardware. The simulation imports the control software, not the other way around.

---

## Simulation

The simulation provides a physics-based model of grease behavior for testing and demonstration purposes.

### Physics Model

The simulation models grease using an exponential viscosity relationship:

| Property | At 10°C | At 20°C | At 35°C |
|---|---|---|---|
| Flow rate | 0.430 kg/s | 0.500 kg/s | 0.626 kg/s |
| Drip weight | 174.3 g | 150.0 g | 119.8 g |
| Drip duration | 11.6 s | 10.0 s | 8.0 s |
| Motor time (5 kg) | 11.6 s | 10.0 s | 8.0 s |

These are representative values for simulation purposes. Real machines would have different values discovered through actual calibration.

### Demonstration Scenarios

Three scenarios are included:

**1. Calibration Scenario** — Calibrates the system at 10°C, 20°C, and 35°C. Produces calibration curves showing how flow rate, drip weight, motor time, and drip duration all vary with temperature. Saves the calibration data for use by the other scenarios.

**2. Dispensing Accuracy Scenario** — Uses the calibration data to dispense 0.5, 1.0, 2.0, 5.0, and 8.0 kg at 25°C (a temperature between calibration points). Measures the error caused by linear interpolation over the exponential physics. Demonstrates that the system achieves sub-percent accuracy even with only three calibration points.

**3. Manual vs Automatic Comparison** — Simulates a human operator trying to dispense 1.0 kg manually (watching the scale and trying to stop at the right time) versus the automatic controller. The human is modeled with realistic reaction delay (0.1–0.5 seconds) and reading error (±5 g). Over 20 trials, the automatic controller shows near-zero consistent error while the human shows significant variance.

---

## Future Plans

### Grease Brand Profiles

Currently, calibration data is stored in a single file. A planned enhancement is to support **calibration profiles per grease brand**, allowing the operator to:
- Calibrate once per brand.
- Switch between brands by selecting the appropriate profile.
- Avoid recalibrating when switching between previously calibrated grease types.

This would allow facilities that work with multiple grease brands to switch instantly without downtime for recalibration.

### Additional Considerations

- **Multiple calibration targets**: while the system currently calibrates at a fixed 5 kg target, the architecture supports changing this value. Calibrating at different target weights could improve accuracy for very small or very large dispenses.
- **Calibration aging**: calibration data does not expire, but grease from different production batches may behave slightly differently. Periodic recalibration is recommended.
- **Data logging**: the `DispenseResult` returned by the automatic controller already includes the target weight, temperature, and motor runtime. This data can be logged for quality tracking and traceability.

---

## Running the System

```bash
# Install dependencies
make install

# Run calibration simulation (must run first)
make calibrate

# Run dispensing accuracy simulation
make dispense

# Run manual vs automatic comparison
make compare

# Open interactive notebook (all scenarios in one place)
make notebook

# Verify the control package loads correctly
make check
```

The scenarios must be run in order: calibration first (generates `calibration_data.json`), then dispensing and comparison (both read from that file).
