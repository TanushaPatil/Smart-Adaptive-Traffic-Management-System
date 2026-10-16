"""
Unit Tests for Smart Adaptive Traffic Management System
=======================================================
"""

import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from smart_traffic.traffic_logic import (
    TrafficLogic, ROADS, MIN_VEHICLES, MAX_VEHICLES, MIN_GREEN, MAX_GREEN
)
from smart_traffic.emergency import EmergencyManager
from smart_traffic.signal_controller import (
    SignalController, SignalPhase, SignalColor
)


class TestTrafficLogic(unittest.TestCase):
    def setUp(self):
        self.logic = TrafficLogic(default_count=10)

    def test_duration_boundaries(self):
        self.logic.set_vehicle_count("North", 0)
        self.assertEqual(self.logic.calculate_green_duration("North"), MIN_GREEN)

        self.logic.set_vehicle_count("North", 20)
        self.assertEqual(self.logic.calculate_green_duration("North"), 15)

        self.logic.set_vehicle_count("North", 40)
        self.assertEqual(self.logic.calculate_green_duration("North"), MAX_GREEN)

    def test_clamping(self):
        self.assertEqual(self.logic.set_vehicle_count("East", -10), 0)
        self.assertEqual(self.logic.set_vehicle_count("West", 999), 40)

    def test_density_classification(self):
        self.logic.set_vehicle_count("South", 5)
        self.assertEqual(self.logic.get_density("South"), "LOW")

        self.logic.set_vehicle_count("South", 20)
        self.assertEqual(self.logic.get_density("South"), "MEDIUM")

        self.logic.set_vehicle_count("South", 35)
        self.assertEqual(self.logic.get_density("South"), "HIGH")

    def test_starvation_prevention(self):
        self.logic.set_vehicle_count("North", 35)
        self.logic.set_vehicle_count("South", 30)
        self.logic.set_vehicle_count("East", 30)
        self.logic.set_vehicle_count("West", 4)

        self.logic.record_road_served("North")
        self.logic.record_road_served("South")
        self.logic.record_road_served("East")

        next_road = self.logic.select_next_road(current_road="East")
        self.assertEqual(next_road, "West")

    def test_throughput_tracking(self):
        self.assertEqual(self.logic.get_total_cleared(), 0)
        self.logic.decrement_vehicle_count("North", 3)
        self.assertEqual(self.logic.get_total_cleared("North"), 3)
        self.assertEqual(self.logic.get_total_cleared(), 3)
        self.assertEqual(self.logic.get_vehicle_count("North"), 7)

        self.logic.reset(default_count=5)
        self.assertEqual(self.logic.get_total_cleared(), 0)

    def test_waiting_cycles_metrics(self):
        self.logic.record_road_served("North")
        self.assertEqual(self.logic.get_waiting_cycles("North"), 0)
        self.assertEqual(self.logic.get_waiting_cycles("South"), 1)
        self.assertGreater(self.logic.get_average_waiting_cycles(), 0.0)


class TestEmergencyManager(unittest.TestCase):
    def setUp(self):
        self.em = EmergencyManager()

    def test_emergency_toggle(self):
        self.assertFalse(self.em.has_emergency())
        self.em.set_emergency("North", True)
        self.assertTrue(self.em.has_emergency())
        self.assertTrue(self.em.is_emergency("North"))
        self.assertFalse(self.em.is_emergency("South"))

        self.em.clear_all()
        self.assertFalse(self.em.has_emergency())

    def test_fifo_priority(self):
        self.em.set_emergency("East", True)
        self.em.set_emergency("North", True)
        self.assertEqual(self.em.get_priority_road(), "East")


class TestSignalController(unittest.TestCase):
    def setUp(self):
        self.controller = SignalController(
            select_road_fn=lambda cur: ("North" if cur != "North" else "South", 5)
        )

    def test_initial_state(self):
        self.assertEqual(self.controller.phase, SignalPhase.ALL_RED)
        self.assertEqual(self.controller.seconds_left, 1)
        for r in ROADS:
            self.assertEqual(self.controller.signals[r], SignalColor.RED)

    def test_cycle_flow(self):
        # 1 tick to complete ALL_RED -> GREEN (5s)
        self.controller.tick()
        self.assertEqual(self.controller.phase, SignalPhase.GREEN)
        self.assertEqual(self.controller.seconds_left, 5)

        # 5 ticks of GREEN -> YELLOW (2s)
        for _ in range(5):
            self.controller.tick()
        self.assertEqual(self.controller.phase, SignalPhase.YELLOW)
        self.assertEqual(self.controller.seconds_left, 2)

        # 2 ticks of YELLOW -> ALL_RED (1s)
        for _ in range(2):
            self.controller.tick()
        self.assertEqual(self.controller.phase, SignalPhase.ALL_RED)
        self.assertEqual(self.controller.seconds_left, 1)

    def test_pause_resume(self):
        self.controller.tick()  # GREEN (5s)
        self.controller.toggle_pause()
        self.assertTrue(self.controller.is_paused)
        self.controller.tick()
        self.assertEqual(self.controller.seconds_left, 5)  # Time frozen


class TestSimVehicle(unittest.TestCase):
    def test_queue_creep_and_motion(self):
        from smart_traffic.main import SimVehicle
        veh = SimVehicle(road="North", is_emergency=False)
        veh.queue_index = 0.0
        veh.current_queue_pos = 1.0

        # When vehicle is waiting, update() advances queue position smoothly
        exited = veh.update()
        self.assertFalse(exited)
        self.assertLess(veh.current_queue_pos, 1.0)

        # When moving, progress increases
        veh.is_moving = True
        self.assertEqual(veh.progress, 0.0)
        exited = veh.update()
        self.assertFalse(exited)
        self.assertGreater(veh.progress, 0.0)


if __name__ == "__main__":
    unittest.main()
