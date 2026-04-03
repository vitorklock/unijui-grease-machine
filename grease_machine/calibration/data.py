from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

CALIBRATION_TARGET_KG = 5.0


@dataclass
class CalibrationPoint:
    temperature: float      # °C at time of calibration
    motor_on_time: float    # seconds from start until scale reads CALIBRATION_TARGET_KG
    drip_weight: float      # kg added to container after motor stopped (post-stabilization)

    @property
    def flow_rate(self) -> float:
        """kg/s — derived from calibration target and motor on time."""
        return CALIBRATION_TARGET_KG / self.motor_on_time

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "motor_on_time": self.motor_on_time,
            "drip_weight": self.drip_weight,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CalibrationPoint:
        return cls(
            temperature=data["temperature"],
            motor_on_time=data["motor_on_time"],
            drip_weight=data["drip_weight"],
        )


class CalibrationStore:
    def __init__(self) -> None:
        self._points: list[CalibrationPoint] = []

    @property
    def points(self) -> list[CalibrationPoint]:
        return list(self._points)

    def add_point(self, point: CalibrationPoint) -> None:
        self._points.append(point)
        self._points.sort(key=lambda p: p.temperature)

    def clear(self) -> None:
        """Clear all calibration data — use after hardware changes."""
        self._points.clear()

    def save(self, path: str | Path) -> None:
        data = [p.to_dict() for p in self._points]
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> CalibrationStore:
        store = cls()
        raw = json.loads(Path(path).read_text())
        for item in raw:
            store.add_point(CalibrationPoint.from_dict(item))
        return store
