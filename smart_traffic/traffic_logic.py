"""
Traffic Logic Module
====================
Calculates dynamic green duration based on traffic density and
schedules the next road fairly to prevent starvation.
"""

from typing import Dict, List, Optional, Tuple

ROADS: Tuple[str, ...] = ("North", "South", "East", "West")
MIN_VEHICLES: int = 0
MAX_VEHICLES: int = 40
MIN_GREEN: int = 5
MAX_GREEN: int = 25


class TrafficLogic:
    """
    Manages vehicle counts, density classification, dynamic green timing,
    and starvation-free road selection.
    """

    def __init__(self, default_count: int = 10) -> None:
        self._counts: Dict[str, int] = {road: default_count for road in ROADS}
        self._waiting_cycles: Dict[str, int] = {road: 0 for road in ROADS}
        self._total_cleared: Dict[str, int] = {road: 0 for road in ROADS}
        self._rotation_index: int = 0

    def set_vehicle_count(self, road: str, count: int) -> int:
        """Clamp vehicle count between 0 and 40."""
        if road not in ROADS:
            return 0
        clamped = max(MIN_VEHICLES, min(MAX_VEHICLES, int(count)))
        self._counts[road] = clamped
        return clamped

    def get_vehicle_count(self, road: str) -> int:
        """Get current vehicle count for a road."""
        return self._counts.get(road, 0)

    def get_all_counts(self) -> Dict[str, int]:
        """Return a copy of all road counts."""
        return dict(self._counts)

    def decrement_vehicle_count(self, road: str, amount: int = 1) -> int:
        """Decrement vehicle count when a vehicle departs (minimum 0) and track throughput."""
        current = self.get_vehicle_count(road)
        actual_departed = min(current, max(0, amount))
        if road in self._total_cleared:
            self._total_cleared[road] += actual_departed
        return self.set_vehicle_count(road, max(0, current - amount))

    def get_total_cleared(self, road: Optional[str] = None) -> int:
        """Return total vehicles cleared for a specific road or across all roads."""
        if road is not None:
            return self._total_cleared.get(road, 0)
        return sum(self._total_cleared.values())

    def get_waiting_cycles(self, road: str) -> int:
        """Return the number of unserved cycles a road has been waiting."""
        return self._waiting_cycles.get(road, 0)

    def get_average_waiting_cycles(self) -> float:
        """Return average waiting cycles across all roads with waiting traffic."""
        waiting_roads = [r for r in ROADS if self._counts[r] > 0]
        if not waiting_roads:
            return 0.0
        return sum(self._waiting_cycles[r] for r in waiting_roads) / len(waiting_roads)

    def get_density(self, road: str) -> str:
        """
        Classify traffic density:
        - LOW: 0 to 12
        - MEDIUM: 13 to 26
        - HIGH: 27 to 40
        """
        count = self.get_vehicle_count(road)
        if count <= 12:
            return "LOW"
        elif count <= 26:
            return "MEDIUM"
        return "HIGH"

    def calculate_green_duration(self, road: str) -> int:
        """
        Calculate green duration from 5s (0 vehicles) to 25s (40 vehicles).
        """
        count = self.get_vehicle_count(road)
        duration = MIN_GREEN + round((count / MAX_VEHICLES) * (MAX_GREEN - MIN_GREEN))
        return max(MIN_GREEN, min(MAX_GREEN, duration))

    def select_next_road(self, current_road: Optional[str]) -> str:
        """
        Select the next road using traffic count + waiting turns (anti-starvation).
        """
        candidates = [r for r in ROADS if r != current_road]
        if not candidates:
            candidates = list(ROADS)

        # Starvation check: roads with traffic waiting >= 3 turns get high priority
        starved = [r for r in candidates if self._waiting_cycles[r] >= 3 and self._counts[r] > 0]
        if starved:
            return max(starved, key=lambda r: (self._waiting_cycles[r], self._counts[r]))

        # Normal priority score: count + (waiting_turns * 5)
        def priority_score(road: str) -> int:
            return self._counts[road] + (self._waiting_cycles[road] * 5)

        highest_score = max(priority_score(r) for r in candidates)
        tied = [r for r in candidates if priority_score(r) == highest_score]

        # Fair rotating tie-breaker
        start = (ROADS.index(current_road) + 1) % len(ROADS) if current_road in ROADS else self._rotation_index
        ordered = ROADS[start:] + ROADS[:start]
        for road in ordered:
            if road in tied:
                self._rotation_index = (ROADS.index(road) + 1) % len(ROADS)
                return road

        return tied[0]

    def record_road_served(self, served_road: str) -> None:
        """Reset waiting cycles for served road and increment for others."""
        if served_road not in ROADS:
            return
        self._waiting_cycles[served_road] = 0
        for road in ROADS:
            if road != served_road:
                self._waiting_cycles[road] += 1

    def reset(self, default_count: int = 10) -> None:
        """Reset all counts, cleared throughput, and waiting history."""
        self._counts = {road: default_count for road in ROADS}
        self._waiting_cycles = {road: 0 for road in ROADS}
        self._total_cleared = {road: 0 for road in ROADS}
        self._rotation_index = 0
