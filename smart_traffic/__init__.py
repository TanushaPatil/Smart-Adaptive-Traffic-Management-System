"""
Smart Adaptive Traffic Management System Package
"""

from .traffic_logic import TrafficLogic, ROADS, MIN_VEHICLES, MAX_VEHICLES, MIN_GREEN, MAX_GREEN
from .emergency import EmergencyManager
from .signal_controller import SignalController, SignalPhase, SignalColor

__all__ = [
    "TrafficLogic",
    "ROADS",
    "MIN_VEHICLES",
    "MAX_VEHICLES",
    "MIN_GREEN",
    "MAX_GREEN",
    "EmergencyManager",
    "SignalController",
    "SignalPhase",
    "SignalColor",
]
