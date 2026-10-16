"""
Emergency Vehicle Priority Module
=================================
Manages emergency vehicle requests and deterministic preemption selection.
"""

from typing import Dict, List, Optional, Tuple

ROADS: Tuple[str, ...] = ("North", "South", "East", "West")


class EmergencyManager:
    """
    Tracks emergency vehicles on each road and determines priority.
    
    Deterministic Selection Rule:
    When multiple roads have emergency vehicles:
    1. First requested (FIFO order).
    2. Road with higher vehicle count (if requested together).
    3. Fixed directional order: North -> South -> East -> West.
    """

    def __init__(self) -> None:
        self._emergencies: Dict[str, bool] = {road: False for road in ROADS}
        self._request_order: List[str] = []

    def set_emergency(self, road: str, active: bool) -> None:
        """Set or clear an emergency vehicle for a road."""
        if road not in ROADS:
            return

        self._emergencies[road] = active
        if active and road not in self._request_order:
            self._request_order.append(road)
        elif not active and road in self._request_order:
            self._request_order.remove(road)

    def is_emergency(self, road: str) -> bool:
        """Check if a road has an emergency vehicle."""
        return self._emergencies.get(road, False)

    def has_emergency(self) -> bool:
        """Check if any road has an active emergency."""
        return any(self._emergencies.values())

    def clear_emergency(self, road: str) -> None:
        """Clear emergency on a specific road."""
        self.set_emergency(road, False)

    def clear_all(self) -> None:
        """Clear all active emergencies."""
        for road in ROADS:
            self._emergencies[road] = False
        self._request_order.clear()

    def get_priority_road(self, traffic_counts: Optional[Dict[str, int]] = None) -> Optional[str]:
        """
        Return the road that should receive emergency green priority.
        Follows FIFO order, using traffic count as tie-breaker.
        """
        active_roads = [r for r in self._request_order if self._emergencies.get(r, False)]
        if not active_roads:
            return None

        if len(active_roads) == 1:
            return active_roads[0]

        # If multiple, the first in FIFO order has priority
        # Tie-break (if needed) with traffic counts
        counts = traffic_counts or {}
        return max(active_roads, key=lambda r: (active_roads.index(r) == 0, counts.get(r, 0)))

    def get_status_text(self, traffic_counts: Optional[Dict[str, int]] = None) -> str:
        """Return a simple display string for the GUI."""
        priority_road = self.get_priority_road(traffic_counts)
        if priority_road:
            return f"🚨 EMERGENCY PRIORITY: {priority_road.upper()} ROAD"
        return "No Active Emergency"
