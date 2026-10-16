"""
Signal Controller Module
========================
State machine for traffic signal phases:
ALL_RED (1s) -> GREEN (5-25s) -> YELLOW (2s) -> ALL_RED (1s)
"""

from enum import Enum
from typing import Callable, Dict, Optional, Tuple

ROADS: Tuple[str, ...] = ("North", "South", "East", "West")
YELLOW_TIME: int = 2
ALL_RED_TIME: int = 1


class SignalPhase(Enum):
    ALL_RED = "ALL_RED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"


class SignalColor(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class SignalController:
    """
    Controls phase switching, countdowns, and signal lamp states.
    Guarantees that conflicting roads never receive green simultaneously.
    """

    def __init__(
        self,
        select_road_fn: Callable[[Optional[str]], Tuple[str, int]],
        on_road_served_fn: Optional[Callable[[str], None]] = None
    ) -> None:
        self._select_road = select_road_fn
        self._on_road_served = on_road_served_fn

        self.phase: SignalPhase = SignalPhase.ALL_RED
        self.active_road: Optional[str] = None
        self.seconds_left: int = ALL_RED_TIME
        self.is_paused: bool = False
        self.is_emergency_active: bool = False

        self.signals: Dict[str, SignalColor] = {r: SignalColor.RED for r in ROADS}

    def tick(self) -> None:
        """Advance the timer by 1 second. Called by Tkinter after()."""
        if self.is_paused:
            return

        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self._next_phase()

    def _next_phase(self) -> None:
        """Cycle through ALL_RED -> GREEN -> YELLOW -> ALL_RED."""
        if self.phase == SignalPhase.ALL_RED:
            # Transition to GREEN for next road
            next_road, duration = self._select_road(self.active_road)
            self.phase = SignalPhase.GREEN
            self.active_road = next_road
            self.seconds_left = max(1, duration)

            for r in ROADS:
                self.signals[r] = SignalColor.GREEN if r == next_road else SignalColor.RED

        elif self.phase == SignalPhase.GREEN:
            # Transition to YELLOW for the active road
            self.phase = SignalPhase.YELLOW
            self.seconds_left = YELLOW_TIME

            for r in ROADS:
                self.signals[r] = SignalColor.YELLOW if r == self.active_road else SignalColor.RED

        elif self.phase == SignalPhase.YELLOW:
            # Transition to ALL_RED safety interlock
            if self.active_road and self._on_road_served:
                self._on_road_served(self.active_road)

            self.phase = SignalPhase.ALL_RED
            self.seconds_left = ALL_RED_TIME

            for r in ROADS:
                self.signals[r] = SignalColor.RED

    def request_preemption(self, emergency_road: str) -> None:
        """
        Safely curtail current green if an emergency occurs on a conflicting road.
        Never skips the yellow or all-red clearance.
        """
        if self.phase == SignalPhase.GREEN and self.active_road != emergency_road:
            if self.seconds_left > 3:
                self.seconds_left = 3

    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns True if now running, False if paused."""
        self.is_paused = not self.is_paused
        return not self.is_paused

    def reset(self) -> None:
        """Reset to the initial safe state."""
        self.phase = SignalPhase.ALL_RED
        self.active_road = None
        self.seconds_left = ALL_RED_TIME
        self.is_paused = False
        self.is_emergency_active = False
        for r in ROADS:
            self.signals[r] = SignalColor.RED
