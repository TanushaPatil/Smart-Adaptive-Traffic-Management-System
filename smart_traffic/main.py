"""
Smart Adaptive Traffic Management System — Interactive Simulation
=================================================================
A visual 4-way intersection simulation featuring:
- Permanent Left-Hand Traffic (LHT) rules (India, UK, Australia, Japan)
- Realistic 3-aspect traffic signals (Red, Amber, Green) on approaching left kerbs
- Zebra pedestrian crosswalks & directional asphalt markings
- Direction-aware vehicles with front headlights, windshields, & brake lights
- Dual-pulse emergency vehicle strobes with siren audio-visual alerts
- Smooth multi-car platooning & queue rolling advance (no teleporting/desync)
- Continuous Auto-Traffic Inflow Mode for autonomous testing
- Live Intersection Analytics HUD (throughput, delay, starvation shield)
- Adaptive green timing formula and fair starvation-free scheduling
"""

import math
import os
import random
import sys
import tkinter as tk
from typing import Dict, List, Optional, Tuple

# Support direct and module runs
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

# Realistic Traffic Simulation Palette
THEME = {
    "bg": "#111215",           # Deep dark charcoal backdrop
    "hud_bg": "#1b1c21",       # Clean elevated container
    "hud_border": "#2c2d35",   # Subtle border
    "text_primary": "#f8fafc", # Clean white text
    "text_muted": "#94a3b8",   # Neutral slate text
    "asphalt": "#222328",      # Realistic dark asphalt road surface
    "lane_line": "#eab308",    # Highway yellow center divider
    "stop_line": "#f8fafc",    # Solid white stop lines
    "zebra": "#f1f5f9",        # High-contrast zebra crosswalk stripes
    "curb": "#2e3038",         # Sidewalk kerb border
    "grass": "#131713",        # Deep dark roadside verge
    "red": "#ef4444",          # Stop signal red
    "red_glow": "#991b1b",
    "red_dark": "#2b0d0d",     # Unlit red bulb
    "yellow": "#f59e0b",       # Amber warning
    "yellow_glow": "#92400e",
    "yellow_dark": "#332205",  # Unlit amber bulb
    "green": "#10b981",        # Go green
    "green_glow": "#065f46",
    "green_dark": "#052617",   # Unlit green bulb
    "amber": "#fbbf24",        # Amber accent for timer
    "btn_bg": "#272830",       # Button background
    "btn_hover": "#373844"     # Button hover
}

# Authentic road vehicle colors
CAR_COLORS = [
    "#f8fafc",  # White
    "#94a3b8",  # Silver / Gray
    "#334155",  # Dark Charcoal
    "#b91c1c",  # Deep Red
    "#d97706",  # Amber Cab
    "#15803d",  # Forest Green
    "#0284c7"   # Sapphire Blue
]


class SimVehicle:
    """Represents an animated vehicle on the intersection canvas."""

    def __init__(self, road: str, is_emergency: bool = False, color: str = "#f8fafc") -> None:
        self.road: str = road
        self.is_emergency: bool = is_emergency
        self.base_color: str = color
        self.color: str = "#dc2626" if is_emergency else color
        self.is_moving: bool = False
        self.has_counted_departure: bool = False
        self.progress: float = 0.0  # 0.0 = waiting at stop line, >0 = crossing intersection
        self.queue_index: float = 0.0
        self.current_queue_pos: float = 0.0

    def update(self, speed: float = 0.038) -> bool:
        """
        Advance vehicle if moving or smoothly creep forward in queue.
        Returns True if vehicle has completely exited the canvas.
        """
        if self.is_moving:
            self.progress += speed
            if self.progress >= 2.6:
                return True
        else:
            # Smoothly advance forward in queue when vehicles ahead depart
            if self.current_queue_pos > self.queue_index:
                self.current_queue_pos = max(self.queue_index, self.current_queue_pos - 0.07)
            elif self.current_queue_pos < self.queue_index:
                self.current_queue_pos = min(self.queue_index, self.current_queue_pos + 0.07)
        return False


class SmartTrafficApp:
    """Visual Traffic Simulation Application with Left-Hand Traffic (LHT)."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Smart Adaptive Traffic Management System (LHT)")
        self.root.geometry("1060x800")
        self.root.minsize(960, 720)
        self.root.configure(bg=THEME["bg"])

        # Core Simulation Logic
        self.traffic = TrafficLogic(default_count=8)
        self.emergency = EmergencyManager()
        self.controller = SignalController(
            select_road_fn=self._select_next_road,
            on_road_served_fn=self._on_road_served
        )

        # Simulation & Animation State
        self.vehicles: Dict[str, List[SimVehicle]] = {road: [] for road in ROADS}
        self.beacon_pulse: bool = False
        self.auto_flow_enabled: bool = False
        self.auto_flow_counter: int = 0

        # UI References
        self.road_widgets: Dict[str, dict] = {}

        self._build_ui()
        self._sync_vehicles_with_counts()

        # Non-blocking event loops
        self._schedule_clock_tick()
        self._schedule_animation_frame()

    # -------------------------------------------------------------------------
    # UI Layout (Clean & Uncluttered)
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        # 1. Top HUD Banner
        hud = tk.Frame(
            self.root, bg=THEME["hud_bg"], padx=18, pady=10,
            highlightbackground=THEME["hud_border"], highlightthickness=1
        )
        hud.pack(fill="x", padx=14, pady=(10, 4))

        # Title & Phase
        title_box = tk.Frame(hud, bg=THEME["hud_bg"])
        title_box.pack(side="left")

        title_row = tk.Frame(title_box, bg=THEME["hud_bg"])
        title_row.pack(anchor="w")

        tk.Label(
            title_row,
            text="SMART TRAFFIC INTERSECTION",
            font=("Segoe UI", 13, "bold"),
            fg=THEME["text_primary"],
            bg=THEME["hud_bg"]
        ).pack(side="left")

        # LHT Badge
        tk.Label(
            title_row,
            text=" 🇬🇧 LHT (DRIVE LEFT) ",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#0c4a6e",
            padx=4,
            pady=1
        ).pack(side="left", padx=8)

        self.phase_status_lbl = tk.Label(
            title_box,
            text="PHASE: ALL RED CLEARANCE",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["red"],
            bg=THEME["hud_bg"]
        )
        self.phase_status_lbl.pack(anchor="w", pady=(2, 0))

        # Countdown Timer (Large Display)
        timer_box = tk.Frame(hud, bg=THEME["hud_bg"])
        timer_box.pack(side="left", padx=20)

        tk.Label(
            timer_box, text="TIME REMAINING",
            font=("Segoe UI", 8, "bold"), fg=THEME["text_muted"], bg=THEME["hud_bg"]
        ).pack(anchor="w")
        self.timer_val_lbl = tk.Label(
            timer_box, text="1 s",
            font=("Segoe UI", 18, "bold"), fg=THEME["amber"], bg=THEME["hud_bg"]
        )
        self.timer_val_lbl.pack(anchor="w")

        # Live Analytics Metrics Banner (Center)
        stats_box = tk.Frame(hud, bg=THEME["hud_bg"])
        stats_box.pack(side="left", padx=10)

        stats_row = tk.Frame(stats_box, bg=THEME["hud_bg"])
        stats_row.pack(anchor="w")

        self.cleared_stat_lbl = tk.Label(
            stats_row,
            text="⚡ Cleared: 0",
            font=("Segoe UI", 9, "bold"),
            fg="#34d399",
            bg="#064e3b",
            padx=6,
            pady=2
        )
        self.cleared_stat_lbl.pack(side="left", padx=3)

        self.delay_stat_lbl = tk.Label(
            stats_row,
            text="⏳ Delay: 0.0 turns",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#1e293b",
            padx=6,
            pady=2
        )
        self.delay_stat_lbl.pack(side="left", padx=3)

        self.starvation_stat_lbl = tk.Label(
            stats_row,
            text="🛡️ Starvation: Safe",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#075985",
            padx=6,
            pady=2
        )
        self.starvation_stat_lbl.pack(side="left", padx=3)

        # Priority & Emergency Status (Right Side)
        em_box = tk.Frame(hud, bg=THEME["hud_bg"])
        em_box.pack(side="right")

        tk.Label(
            em_box, text="PRIORITY SCHEDULING",
            font=("Segoe UI", 8, "bold"), fg=THEME["text_muted"], bg=THEME["hud_bg"]
        ).pack(anchor="e")
        self.emergency_status_lbl = tk.Label(
            em_box,
            text="Adaptive Density Scheduling",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text_muted"],
            bg=THEME["hud_bg"]
        )
        self.emergency_status_lbl.pack(anchor="e")

        # 2. Main Simulation Canvas Container
        sim_container = tk.Frame(self.root, bg=THEME["bg"])
        sim_container.pack(fill="both", expand=True, padx=14, pady=4)

        self.canvas = tk.Canvas(
            sim_container,
            bg=THEME["grass"],
            highlightthickness=1,
            highlightbackground=THEME["hud_border"]
        )
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.canvas.bind("<Configure>", lambda e: self._render_canvas())

        # 3. Approach Controls (Right Panel)
        side_panel = tk.Frame(sim_container, bg=THEME["bg"], width=270)
        side_panel.pack(side="right", fill="y")
        self._build_road_panels(side_panel)

        # 4. Clean Bottom Action Bar
        self._build_bottom_controls()

    def _build_road_panels(self, parent: tk.Frame) -> None:
        """Create clean control cards for North, South, East, West."""
        tk.Label(
            parent,
            text="APPROACH CONTROL (LHT)",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text_muted"],
            bg=THEME["bg"]
        ).pack(anchor="w", pady=(0, 6))

        for road in ROADS:
            card = tk.Frame(
                parent, bg=THEME["hud_bg"], padx=10, pady=8,
                highlightbackground=THEME["hud_border"], highlightthickness=1
            )
            card.pack(fill="x", pady=4)

            # Top: Road name & Signal Pill
            hdr = tk.Frame(card, bg=THEME["hud_bg"])
            hdr.pack(fill="x", pady=(0, 4))

            tk.Label(
                hdr, text=f"{road.upper()}",
                font=("Segoe UI", 11, "bold"), fg=THEME["text_primary"], bg=THEME["hud_bg"]
            ).pack(side="left")

            signal_pill = tk.Label(
                hdr, text="STOP", font=("Segoe UI", 9, "bold"),
                fg=THEME["red"], bg="#450a0a", padx=7, pady=1
            )
            signal_pill.pack(side="right")

            # Mid: Density & Green Duration
            mid = tk.Frame(card, bg=THEME["hud_bg"])
            mid.pack(fill="x", pady=(0, 6))

            density_lbl = tk.Label(
                mid, text="LOW (8 cars)", font=("Segoe UI", 9),
                fg=THEME["green"], bg=THEME["hud_bg"]
            )
            density_lbl.pack(side="left")

            duration_lbl = tk.Label(
                mid, text="Green: 9s", font=("Segoe UI", 9, "bold"),
                fg=THEME["text_primary"], bg=THEME["hud_bg"]
            )
            duration_lbl.pack(side="right")

            # Controls: Count [-] [+] and Emergency Toggle
            ctrls = tk.Frame(card, bg=THEME["hud_bg"])
            ctrls.pack(fill="x")

            btn_minus = tk.Button(
                ctrls, text="−", width=2, bg=THEME["btn_bg"], fg="white", relief="flat",
                activebackground=THEME["btn_hover"], activeforeground="white",
                command=lambda r=road: self._adjust_traffic(r, -2)
            )
            btn_minus.pack(side="left")

            count_lbl = tk.Label(
                ctrls, text="8", font=("Segoe UI", 10, "bold"),
                fg="white", bg=THEME["hud_bg"], width=4
            )
            count_lbl.pack(side="left", padx=4)

            btn_plus = tk.Button(
                ctrls, text="+", width=2, bg=THEME["btn_bg"], fg="white", relief="flat",
                activebackground=THEME["btn_hover"], activeforeground="white",
                command=lambda r=road: self._adjust_traffic(r, +2)
            )
            btn_plus.pack(side="left")

            em_btn = tk.Button(
                ctrls,
                text="🚨 Emergency",
                font=("Segoe UI", 8, "bold"),
                bg=THEME["btn_bg"],
                fg=THEME["text_muted"],
                relief="flat",
                activebackground="#991b1b",
                activeforeground="white",
                padx=6,
                command=lambda r=road: self._toggle_emergency(r)
            )
            em_btn.pack(side="right")

            self.road_widgets[road] = {
                "signal_pill": signal_pill,
                "density_lbl": density_lbl,
                "duration_lbl": duration_lbl,
                "count_lbl": count_lbl,
                "em_btn": em_btn
            }

    def _build_bottom_controls(self) -> None:
        """Create bottom action bar with simulation controls."""
        bar = tk.Frame(self.root, bg=THEME["hud_bg"], padx=14, pady=8)
        bar.pack(fill="x", padx=14, pady=(4, 10))

        self.pause_btn = tk.Button(
            bar,
            text="⏸ Pause Simulation",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg="white",
            relief="flat",
            activebackground=THEME["btn_hover"],
            activeforeground="white",
            padx=12,
            pady=4,
            command=self._toggle_pause
        )
        self.pause_btn.pack(side="left", padx=4)

        self.auto_flow_btn = tk.Button(
            bar,
            text="🚗 Auto Traffic Flow: OFF",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text_muted"],
            relief="flat",
            activebackground="#059669",
            activeforeground="white",
            padx=10,
            pady=4,
            command=self._toggle_auto_flow
        )
        self.auto_flow_btn.pack(side="left", padx=4)

        tk.Button(
            bar,
            text="🎲 Randomize Traffic",
            font=("Segoe UI", 9),
            bg=THEME["btn_bg"],
            fg="white",
            relief="flat",
            activebackground=THEME["btn_hover"],
            activeforeground="white",
            padx=10,
            pady=4,
            command=self._randomize_traffic
        ).pack(side="left", padx=4)

        tk.Button(
            bar,
            text="🚨 Clear Emergencies",
            font=("Segoe UI", 9),
            bg="#7f1d1d",
            fg="white",
            relief="flat",
            activebackground="#991b1b",
            activeforeground="white",
            padx=10,
            pady=4,
            command=self._clear_emergencies
        ).pack(side="left", padx=4)

        tk.Button(
            bar,
            text="🔄 Reset Simulation",
            font=("Segoe UI", 9),
            bg=THEME["btn_bg"],
            fg="white",
            relief="flat",
            activebackground=THEME["btn_hover"],
            activeforeground="white",
            padx=10,
            pady=4,
            command=self._reset_simulation
        ).pack(side="right", padx=4)

    # -------------------------------------------------------------------------
    # Vehicle Queue & Synchronization (Desync Bug Fixed)
    # -------------------------------------------------------------------------

    def _sync_vehicles_with_counts(self) -> None:
        """
        Keep waiting vehicle instances aligned with logic counts without
        disturbing moving vehicles that are in-flight across the intersection.
        """
        for road in ROADS:
            target_count = self.traffic.get_vehicle_count(road)
            is_em = self.emergency.is_emergency(road)
            all_list = self.vehicles[road]

            # Filter waiting vehicles
            waiting = [v for v in all_list if not v.is_moving]

            # Add missing waiting vehicles
            while len(waiting) < target_count:
                color = random.choice(CAR_COLORS)
                new_veh = SimVehicle(road=road, is_emergency=False, color=color)
                idx = len(waiting)
                new_veh.queue_index = float(idx)
                new_veh.current_queue_pos = float(idx)
                all_list.append(new_veh)
                waiting.append(new_veh)

            # Remove excess waiting vehicles from back of queue
            while len(waiting) > target_count:
                veh_to_remove = waiting.pop()
                if veh_to_remove in all_list:
                    all_list.remove(veh_to_remove)

            # Re-index waiting vehicles
            for idx, veh in enumerate(waiting):
                veh.queue_index = float(idx)

            # Apply emergency status to front waiting vehicle
            if waiting:
                waiting[0].is_emergency = is_em
                waiting[0].color = "#dc2626" if is_em else waiting[0].base_color

    # -------------------------------------------------------------------------
    # Canvas Rendering: Left-Hand Traffic (LHT) Geometry & Markings
    # -------------------------------------------------------------------------

    def _render_canvas(self) -> None:
        """
        Draw Left-Hand Traffic (LHT) crossroads:
        - Vehicles drive on the LEFT side of the road
        - Stop lines cover only the approaching driver's left lane
        - Realistic 3-aspect signals (Red/Amber/Green) on approaching driver's left kerb
        - Zebra pedestrian crossings & directional lane arrows
        """
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50 or h < 50:
            return

        self.canvas.delete("all")
        cx, cy = w / 2, h / 2
        road_w = 110
        half_w = road_w / 2
        lane_offset = 28.0  # Centered in the 55px one-way lane

        # 1. Sidewalk Curb Radii (Curved junction corners)
        curb_rad = 22
        self.canvas.create_rectangle(cx - half_w - curb_rad, cy - half_w - curb_rad, cx - half_w, cy - half_w, fill=THEME["curb"], outline="")
        self.canvas.create_rectangle(cx + half_w, cy - half_w - curb_rad, cx + half_w + curb_rad, cy - half_w, fill=THEME["curb"], outline="")
        self.canvas.create_rectangle(cx - half_w - curb_rad, cy + half_w, cx - half_w, cy + half_w + curb_rad, fill=THEME["curb"], outline="")
        self.canvas.create_rectangle(cx + half_w, cy + half_w, cx + half_w + curb_rad, cy + half_w + curb_rad, fill=THEME["curb"], outline="")

        # 2. Asphalt Roadways
        self.canvas.create_rectangle(cx - half_w, 0, cx + half_w, h, fill=THEME["asphalt"], outline="")
        self.canvas.create_rectangle(0, cy - half_w, w, cy + half_w, fill=THEME["asphalt"], outline="")
        # Intersection Box
        self.canvas.create_rectangle(cx - half_w, cy - half_w, cx + half_w, cy + half_w, fill="#1c1c20", outline="#2e2e34")

        # 3. Highway Yellow Dashed Center Dividers
        dash = (6, 6)
        self.canvas.create_line(cx, 0, cx, cy - half_w - 24, fill=THEME["lane_line"], width=2, dash=dash)
        self.canvas.create_line(cx, cy + half_w + 24, cx, h, fill=THEME["lane_line"], width=2, dash=dash)
        self.canvas.create_line(0, cy, cx - half_w - 24, cy, fill=THEME["lane_line"], width=2, dash=dash)
        self.canvas.create_line(cx + half_w + 24, cy, w, cy, fill=THEME["lane_line"], width=2, dash=dash)

        # 4. Zebra Pedestrian Crossings (All 4 entries)
        self._draw_zebra_crossing(cx, cy, half_w)

        # 5. Stop Lines (LHT: Approaching left lane only)
        # North incoming is on Screen Right (x from cx to cx + half_w)
        self.canvas.create_line(cx, cy - half_w - 6, cx + half_w, cy - half_w - 6, fill=THEME["stop_line"], width=3)
        # South incoming is on Screen Left (x from cx - half_w to cx)
        self.canvas.create_line(cx - half_w, cy + half_w + 6, cx, cy + half_w + 6, fill=THEME["stop_line"], width=3)
        # West incoming is on Screen Top (y from cy - half_w to cy)
        self.canvas.create_line(cx - half_w - 6, cy - half_w, cx - half_w - 6, cy, fill=THEME["stop_line"], width=3)
        # East incoming is on Screen Bottom (y from cy to cy + half_w)
        self.canvas.create_line(cx + half_w + 6, cy, cx + half_w + 6, cy + half_w, fill=THEME["stop_line"], width=3)

        # 6. Directional Lane Arrows (White markings on asphalt)
        self._draw_lane_arrows(cx, cy, half_w, lane_offset)

        # 7. Road Labels (Positioned directly over incoming LHT lanes)
        self.canvas.create_text(cx + lane_offset, 22, text="⬇ NORTH (LHT)", fill=THEME["text_muted"], font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(cx - lane_offset, h - 22, text="⬆ SOUTH (LHT)", fill=THEME["text_muted"], font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(38, cy - lane_offset, text="➡ WEST (LHT)", fill=THEME["text_muted"], font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(w - 38, cy + lane_offset, text="⬅ EAST (LHT)", fill=THEME["text_muted"], font=("Segoe UI", 9, "bold"))

        # 8. Realistic 3-Aspect Traffic Signals (Driver's Left Kerb)
        signal_positions = {
            "North": (cx + half_w + 8, cy - half_w - 52),
            "South": (cx - half_w - 30, cy + half_w + 8),
            "West": (cx - half_w - 52, cy - half_w - 30),
            "East": (cx + half_w + 8, cy + half_w + 10)
        }

        for road, (sx, sy) in signal_positions.items():
            state = self.controller.signals[road]
            self._draw_3aspect_signal(sx, sy, road, state)

        # 9. Render Vehicles (Queued & Crossing)
        self._render_vehicles(cx, cy, half_w, lane_offset, w, h)

    def _draw_zebra_crossing(self, cx: float, cy: float, half_w: float) -> None:
        """Draw pedestrian zebra crossings across roads before stop lines."""
        # North Road crosswalk
        ny1, ny2 = cy - half_w - 22, cy - half_w - 8
        for x in range(int(cx - half_w + 4), int(cx + half_w), 10):
            self.canvas.create_rectangle(x, ny1, x + 6, ny2, fill=THEME["zebra"], outline="")

        # South Road crosswalk
        sy1, sy2 = cy + half_w + 8, cy + half_w + 22
        for x in range(int(cx - half_w + 4), int(cx + half_w), 10):
            self.canvas.create_rectangle(x, sy1, x + 6, sy2, fill=THEME["zebra"], outline="")

        # West Road crosswalk
        wx1, wx2 = cx - half_w - 22, cx - half_w - 8
        for y in range(int(cy - half_w + 4), int(cy + half_w), 10):
            self.canvas.create_rectangle(wx1, y, wx2, y + 6, fill=THEME["zebra"], outline="")

        # East Road crosswalk
        ex1, ex2 = cx + half_w + 8, cx + half_w + 22
        for y in range(int(cy - half_w + 4), int(cy + half_w), 10):
            self.canvas.create_rectangle(ex1, y, ex2, y + 6, fill=THEME["zebra"], outline="")

    def _draw_lane_arrows(self, cx: float, cy: float, half_w: float, lane_offset: float) -> None:
        """Draw directional arrows in incoming and outgoing lanes for visual clarity."""
        arr_col = "#64748b"
        # North incoming (down)
        self.canvas.create_text(cx + lane_offset, cy - half_w - 40, text="↓", fill=arr_col, font=("Segoe UI", 14, "bold"))
        # North outgoing (up)
        self.canvas.create_text(cx - lane_offset, cy - half_w - 40, text="↑", fill="#334155", font=("Segoe UI", 12))

        # South incoming (up)
        self.canvas.create_text(cx - lane_offset, cy + half_w + 40, text="↑", fill=arr_col, font=("Segoe UI", 14, "bold"))
        # South outgoing (down)
        self.canvas.create_text(cx + lane_offset, cy + half_w + 40, text="↓", fill="#334155", font=("Segoe UI", 12))

        # West incoming (right)
        self.canvas.create_text(cx - half_w - 40, cy - lane_offset, text="→", fill=arr_col, font=("Segoe UI", 14, "bold"))
        # West outgoing (left)
        self.canvas.create_text(cx - half_w - 40, cy + lane_offset, text="←", fill="#334155", font=("Segoe UI", 12))

        # East incoming (left)
        self.canvas.create_text(cx + half_w + 40, cy + lane_offset, text="←", fill=arr_col, font=("Segoe UI", 14, "bold"))
        # East outgoing (right)
        self.canvas.create_text(cx + half_w + 40, cy - lane_offset, text="→", fill="#334155", font=("Segoe UI", 12))

    def _draw_3aspect_signal(self, sx: float, sy: float, road: str, state: SignalColor) -> None:
        """Draw realistic 3-lamp traffic signal head (Red, Amber, Green) with active glow."""
        w, h = 22, 54
        # Signal Post Housing
        self.canvas.create_rectangle(sx, sy, sx + w, sy + h, fill="#131316", outline="#3f3f46", width=1)

        # Header Badge
        letter = road[0].upper()
        self.canvas.create_text(sx + w / 2, sy - 8, text=f"[{letter}]", fill=THEME["text_muted"], font=("Segoe UI", 7, "bold"))

        # Lamp 1: RED (Top)
        r_lit = (state == SignalColor.RED)
        r_fill = THEME["red"] if r_lit else THEME["red_dark"]
        r_outline = THEME["red_glow"] if r_lit else "#1a0808"
        self.canvas.create_oval(sx + 4, sy + 4, sx + w - 4, sy + 18, fill=r_fill, outline=r_outline, width=1.5 if r_lit else 1)
        if r_lit:
            self.canvas.create_oval(sx + 8, sy + 8, sx + w - 8, sy + 14, fill="#fca5a5", outline="")

        # Lamp 2: AMBER (Middle)
        y_lit = (state == SignalColor.YELLOW)
        y_fill = THEME["yellow"] if y_lit else THEME["yellow_dark"]
        y_outline = THEME["yellow_glow"] if y_lit else "#211603"
        self.canvas.create_oval(sx + 4, sy + 20, sx + w - 4, sy + 34, fill=y_fill, outline=y_outline, width=1.5 if y_lit else 1)
        if y_lit:
            self.canvas.create_oval(sx + 8, sy + 24, sx + w - 8, sy + 30, fill="#fde68a", outline="")

        # Lamp 3: GREEN (Bottom)
        g_lit = (state == SignalColor.GREEN)
        g_fill = THEME["green"] if g_lit else THEME["green_dark"]
        g_outline = THEME["green_glow"] if g_lit else "#02160d"
        self.canvas.create_oval(sx + 4, sy + 36, sx + w - 4, sy + 50, fill=g_fill, outline=g_outline, width=1.5 if g_lit else 1)
        if g_lit:
            self.canvas.create_oval(sx + 8, sy + 40, sx + w - 8, sy + 46, fill="#6ee7b7", outline="")

    # -------------------------------------------------------------------------
    # Vehicle Rendering & Direction-Aware Graphics
    # -------------------------------------------------------------------------

    def _render_vehicles(self, cx: float, cy: float, half_w: float, lane_offset: float, w: float, h: float) -> None:
        """Draw queued and crossing vehicles for all roads according to LHT rules."""
        gap = 36.0  # Spacing between vehicles in queue

        # North Road (Approaching from top, driving South on Screen Right: cx + lane_offset)
        n_lane = cx + lane_offset
        for veh in self.vehicles["North"]:
            if veh.is_moving:
                y = (cy - half_w - 28) + (veh.progress * (h / 1.6))
            else:
                y = (cy - half_w - 28) - (veh.current_queue_pos * gap)
            if -40 <= y <= h + 40 and veh.current_queue_pos < 7.5:
                self._draw_car(n_lane, y, width=22, length=32, veh=veh, direction="South")

        # South Road (Approaching from bottom, driving North on Screen Left: cx - lane_offset)
        s_lane = cx - lane_offset
        for veh in self.vehicles["South"]:
            if veh.is_moving:
                y = (cy + half_w + 28) - (veh.progress * (h / 1.6))
            else:
                y = (cy + half_w + 28) + (veh.current_queue_pos * gap)
            if -40 <= y <= h + 40 and veh.current_queue_pos < 7.5:
                self._draw_car(s_lane, y, width=22, length=32, veh=veh, direction="North")

        # West Road (Approaching from left, driving East on Screen Top: cy - lane_offset)
        w_lane = cy - lane_offset
        for veh in self.vehicles["West"]:
            if veh.is_moving:
                x = (cx - half_w - 28) + (veh.progress * (w / 1.6))
            else:
                x = (cx - half_w - 28) - (veh.current_queue_pos * gap)
            if -40 <= x <= w + 40 and veh.current_queue_pos < 7.5:
                self._draw_car(x, w_lane, width=32, length=22, veh=veh, direction="East")

        # East Road (Approaching from right, driving West on Screen Bottom: cy + lane_offset)
        e_lane = cy + lane_offset
        for veh in self.vehicles["East"]:
            if veh.is_moving:
                x = (cx + half_w + 28) - (veh.progress * (w / 1.6))
            else:
                x = (cx + half_w + 28) + (veh.current_queue_pos * gap)
            if -40 <= x <= w + 40 and veh.current_queue_pos < 7.5:
                self._draw_car(x, e_lane, width=32, length=22, veh=veh, direction="West")

    def _draw_car(self, x: float, y: float, width: float, length: float, veh: SimVehicle, direction: str) -> None:
        """
        Render a direction-aware car:
        - Front windshield facing the forward travel direction
        - Front bumper headlights (warm yellow-white)
        - Rear bumper taillights (ruby red)
        - Alternating dual-color strobe beacon for emergency vehicles
        """
        hw = width / 2
        hl = length / 2

        # 1. Main Car Body
        self.canvas.create_rectangle(x - hw, y - hl, x + hw, y + hl, fill=veh.color, outline="#18181b", width=1)

        # 2. Roof & Windows tailored to heading direction
        headlight_col = "#fef08a"
        taillight_col = "#dc2626"

        if direction == "South":  # North car moving down (+y)
            # Front Windshield (lower) & Rear Window (upper)
            self.canvas.create_rectangle(x - hw + 3, y + 2, x + hw - 3, y + 7, fill="#0f172a", outline="")
            self.canvas.create_rectangle(x - hw + 4, y - 9, x + hw - 4, y - 5, fill="#1e293b", outline="")
            # Headlights (bottom corners)
            self.canvas.create_rectangle(x - hw + 2, y + hl - 2, x - hw + 5, y + hl, fill=headlight_col, outline="")
            self.canvas.create_rectangle(x + hw - 5, y + hl - 2, x + hw - 2, y + hl, fill=headlight_col, outline="")
            # Taillights (top corners)
            self.canvas.create_rectangle(x - hw + 2, y - hl, x - hw + 5, y - hl + 2, fill=taillight_col, outline="")
            self.canvas.create_rectangle(x + hw - 5, y - hl, x + hw - 2, y - hl + 2, fill=taillight_col, outline="")

        elif direction == "North":  # South car moving up (-y)
            # Front Windshield (upper) & Rear Window (lower)
            self.canvas.create_rectangle(x - hw + 3, y - 7, x + hw - 3, y - 2, fill="#0f172a", outline="")
            self.canvas.create_rectangle(x - hw + 4, y + 5, x + hw - 4, y + 9, fill="#1e293b", outline="")
            # Headlights (top corners)
            self.canvas.create_rectangle(x - hw + 2, y - hl, x - hw + 5, y - hl + 2, fill=headlight_col, outline="")
            self.canvas.create_rectangle(x + hw - 5, y - hl, x + hw - 2, y - hl + 2, fill=headlight_col, outline="")
            # Taillights (bottom corners)
            self.canvas.create_rectangle(x - hw + 2, y + hl - 2, x - hw + 5, y + hl, fill=taillight_col, outline="")
            self.canvas.create_rectangle(x + hw - 5, y + hl - 2, x + hw - 2, y + hl, fill=taillight_col, outline="")

        elif direction == "East":  # West car moving right (+x)
            # Front Windshield (right) & Rear Window (left)
            self.canvas.create_rectangle(x + 2, y - hl + 3, x + 7, y + hl - 3, fill="#0f172a", outline="")
            self.canvas.create_rectangle(x - 9, y - hl + 4, x - 5, y + hl - 4, fill="#1e293b", outline="")
            # Headlights (right corners)
            self.canvas.create_rectangle(x + hw - 2, y - hl + 2, x + hw, y - hl + 5, fill=headlight_col, outline="")
            self.canvas.create_rectangle(x + hw - 2, y + hl - 5, x + hw, y + hl - 2, fill=headlight_col, outline="")
            # Taillights (left corners)
            self.canvas.create_rectangle(x - hw, y - hl + 2, x - hw + 2, y - hl + 5, fill=taillight_col, outline="")
            self.canvas.create_rectangle(x - hw, y + hl - 5, x - hw + 2, y + hl - 2, fill=taillight_col, outline="")

        elif direction == "West":  # East car moving left (-x)
            # Front Windshield (left) & Rear Window (right)
            self.canvas.create_rectangle(x - 7, y - hl + 3, x - 2, y + hl - 3, fill="#0f172a", outline="")
            self.canvas.create_rectangle(x + 5, y - hl + 4, x + 9, y + hl - 4, fill="#1e293b", outline="")
            # Headlights (left corners)
            self.canvas.create_rectangle(x - hw, y - hl + 2, x - hw + 2, y - hl + 5, fill=headlight_col, outline="")
            self.canvas.create_rectangle(x - hw, y + hl - 5, x - hw + 2, y + hl - 2, fill=headlight_col, outline="")
            # Taillights (right corners)
            self.canvas.create_rectangle(x + hw - 2, y - hl + 2, x + hw, y - hl + 5, fill=taillight_col, outline="")
            self.canvas.create_rectangle(x + hw - 2, y + hl - 5, x + hw, y + hl - 2, fill=taillight_col, outline="")

        # 3. Emergency Dual-Strobe Beacon
        if veh.is_emergency:
            left_col = "#ef4444" if self.beacon_pulse else "#3b82f6"
            right_col = "#3b82f6" if self.beacon_pulse else "#ef4444"
            self.canvas.create_oval(x - 6, y - 4, x - 1, y + 4, fill=left_col, outline="")
            self.canvas.create_oval(x + 1, y - 4, x + 6, y + 4, fill=right_col, outline="")
            self.canvas.create_text(x, y - 16, text="🚨", font=("Segoe UI", 9))

    # -------------------------------------------------------------------------
    # Animation Loop (Smooth 30 FPS Motion & Platooning)
    # -------------------------------------------------------------------------

    def _schedule_animation_frame(self) -> None:
        """Run animation loop every 35ms non-blockingly."""
        self._anim_id = self.root.after(35, self._on_anim_frame)

    def _on_anim_frame(self) -> None:
        if not self.root.winfo_exists():
            return

        if not self.controller.is_paused:
            self.beacon_pulse = not self.beacon_pulse

            # Continuous Dispatching during GREEN phase:
            # If active road is GREEN, allow subsequent queued cars to roll out
            active = self.controller.active_road
            if self.controller.phase == SignalPhase.GREEN and active:
                waiting = [v for v in self.vehicles[active] if not v.is_moving]
                moving = [v for v in self.vehicles[active] if v.is_moving]

                # Safe following headway: dispatch next car if front car has progressed
                if waiting:
                    can_dispatch = False
                    if not moving:
                        can_dispatch = True
                    elif all(m.progress > 0.38 for m in moving):
                        can_dispatch = True

                    if can_dispatch:
                        front_car = waiting[0]
                        front_car.is_moving = True
                        # Update target queue positions for remaining waiting cars
                        for idx, v in enumerate(waiting[1:]):
                            v.queue_index = float(idx)

            # Update vehicles moving across the intersection
            for road in ROADS:
                exited_vehicles = []
                for veh in self.vehicles[road]:
                    if veh.is_moving:
                        # Count departure when vehicle reaches center and exits stop line
                        if veh.progress > 0.75 and not veh.has_counted_departure:
                            veh.has_counted_departure = True
                            self.traffic.decrement_vehicle_count(road, 1)
                            self._sync_road_card(road)
                            self._sync_analytics_hud()

                        if veh.update(speed=0.038):
                            exited_vehicles.append(veh)
                    else:
                        veh.update()

                # Cleanly remove exited vehicles
                for v in exited_vehicles:
                    if v in self.vehicles[road]:
                        self.vehicles[road].remove(v)

            self._render_canvas()

        self._schedule_animation_frame()

    # -------------------------------------------------------------------------
    # 1-Second Clock Tick & Signal Controller State Machine
    # -------------------------------------------------------------------------

    def _schedule_clock_tick(self) -> None:
        """Run 1-second clock loop."""
        self._clock_id = self.root.after(1000, self._on_clock_tick)

    def _on_clock_tick(self) -> None:
        if not self.root.winfo_exists():
            return

        self.controller.tick()

        # Handle Auto-Traffic Inflow Mode (Continuous dynamic arrivals)
        if self.auto_flow_enabled and not self.controller.is_paused:
            self.auto_flow_counter += 1
            if self.auto_flow_counter >= 3:
                self.auto_flow_counter = 0
                road_pick = random.choice(ROADS)
                curr_cnt = self.traffic.get_vehicle_count(road_pick)
                if curr_cnt < 28:
                    self.traffic.set_vehicle_count(road_pick, curr_cnt + random.randint(1, 3))
                    self._sync_vehicles_with_counts()

                # Rare emergency vehicle arrival (5% chance if none active)
                if not self.emergency.has_emergency() and random.random() < 0.05:
                    em_road = random.choice(ROADS)
                    self._toggle_emergency(em_road)

        self._sync_hud()
        self._schedule_clock_tick()

    def _select_next_road(self, current_road: Optional[str]) -> Tuple[str, int]:
        """SignalController selector callback with priority preemption & fairness."""
        counts = self.traffic.get_all_counts()

        # Emergency Preemption
        if self.emergency.has_emergency():
            priority_road = self.emergency.get_priority_road(counts)
            if priority_road:
                duration = max(8, self.traffic.calculate_green_duration(priority_road))
                return priority_road, duration

        # Adaptive Traffic Density with Anti-Starvation
        selected = self.traffic.select_next_road(current_road)
        duration = self.traffic.calculate_green_duration(selected)
        return selected, duration

    def _on_road_served(self, served_road: str) -> None:
        """Invoked when a green + yellow phase ends."""
        self.traffic.record_road_served(served_road)

        # Clear served emergency
        if self.emergency.is_emergency(served_road):
            self.emergency.clear_emergency(served_road)

        self._sync_vehicles_with_counts()
        self._sync_all_cards()
        self._sync_analytics_hud()

    # -------------------------------------------------------------------------
    # UI Sync Helpers
    # -------------------------------------------------------------------------

    def _sync_hud(self) -> None:
        phase = self.controller.phase
        active = self.controller.active_road
        secs = max(0, self.controller.seconds_left)

        if phase == SignalPhase.ALL_RED:
            self.phase_status_lbl.configure(text="PHASE: ALL RED CLEARANCE", fg=THEME["red"])
            self.timer_val_lbl.configure(fg=THEME["red"])
        elif phase == SignalPhase.GREEN:
            is_em = self.emergency.is_emergency(active) if active else False
            fg_col = "#dc2626" if is_em else THEME["green"]
            txt = f"PHASE: GREEN — {active.upper()}" + (" (EMERGENCY)" if is_em else "")
            self.phase_status_lbl.configure(text=txt, fg=fg_col)
            self.timer_val_lbl.configure(fg=fg_col)
        elif phase == SignalPhase.YELLOW:
            self.phase_status_lbl.configure(text=f"PHASE: YELLOW CAUTION — {active.upper()}", fg=THEME["yellow"])
            self.timer_val_lbl.configure(fg=THEME["yellow"])

        self.timer_val_lbl.configure(text=f"{secs} s")

        # Emergency priority status banner
        counts = self.traffic.get_all_counts()
        self.emergency_status_lbl.configure(
            text=self.emergency.get_status_text(counts),
            fg="#ef4444" if self.emergency.has_emergency() else THEME["text_muted"]
        )

        self._sync_all_cards()
        self._sync_analytics_hud()

    def _sync_analytics_hud(self) -> None:
        """Update live intersection throughput and wait statistics."""
        cleared = self.traffic.get_total_cleared()
        avg_delay = self.traffic.get_average_waiting_cycles()
        self.cleared_stat_lbl.configure(text=f"⚡ Cleared: {cleared}")
        self.delay_stat_lbl.configure(text=f"⏳ Delay: {avg_delay:.1f} turns")

        # Starvation check
        starved_roads = [r for r in ROADS if self.traffic.get_waiting_cycles(r) >= 3 and self.traffic.get_vehicle_count(r) > 0]
        if starved_roads:
            self.starvation_stat_lbl.configure(
                text=f"⚠️ Starvation: {starved_roads[0].upper()} PRIORITY",
                fg="#fef08a",
                bg="#854d0e"
            )
        else:
            self.starvation_stat_lbl.configure(
                text="🛡️ Starvation: Safe",
                fg="#38bdf8",
                bg="#075985"
            )

    def _sync_road_card(self, road: str) -> None:
        w = self.road_widgets[road]
        count = self.traffic.get_vehicle_count(road)
        density = self.traffic.get_density(road)
        calc_green = self.traffic.calculate_green_duration(road)
        sig = self.controller.signals[road]
        is_em = self.emergency.is_emergency(road)

        # Signal Pill
        if sig == SignalColor.GREEN:
            w["signal_pill"].configure(text="GO", fg=THEME["green"], bg="#064e3b")
        elif sig == SignalColor.YELLOW:
            w["signal_pill"].configure(text="WAIT", fg=THEME["yellow"], bg="#78350f")
        else:
            w["signal_pill"].configure(text="STOP", fg=THEME["red"], bg="#450a0a")

        # Density & Count
        w["count_lbl"].configure(text=str(count))
        w["density_lbl"].configure(
            text=f"{density} ({count} cars)",
            fg=THEME["green"] if density == "LOW" else (THEME["yellow"] if density == "MEDIUM" else THEME["red"])
        )
        w["duration_lbl"].configure(text=f"Green: {calc_green}s")

        # Emergency Button
        w["em_btn"].configure(
            bg="#991b1b" if is_em else THEME["btn_bg"],
            fg="white" if is_em else THEME["text_muted"]
        )

    def _sync_all_cards(self) -> None:
        for r in ROADS:
            self._sync_road_card(r)

    # -------------------------------------------------------------------------
    # User Actions & Interactive Controls
    # -------------------------------------------------------------------------

    def _adjust_traffic(self, road: str, delta: int) -> None:
        """Add or remove vehicles on a road."""
        curr = self.traffic.get_vehicle_count(road)
        new_val = max(MIN_VEHICLES, min(MAX_VEHICLES, curr + delta))
        self.traffic.set_vehicle_count(road, new_val)
        self._sync_vehicles_with_counts()
        self._sync_hud()

    def _toggle_emergency(self, road: str) -> None:
        """Toggle emergency vehicle on a road with safe preemption."""
        is_active = not self.emergency.is_emergency(road)
        self.emergency.set_emergency(road, is_active)
        if is_active:
            self.controller.request_preemption(road)
        self._sync_vehicles_with_counts()
        self._sync_hud()

    def _toggle_auto_flow(self) -> None:
        """Toggle continuous automatic inbound traffic generator."""
        self.auto_flow_enabled = not self.auto_flow_enabled
        if self.auto_flow_enabled:
            self.auto_flow_btn.configure(
                text="🚗 Auto Traffic Flow: ON",
                bg="#059669",
                fg="white"
            )
        else:
            self.auto_flow_btn.configure(
                text="🚗 Auto Traffic Flow: OFF",
                bg=THEME["btn_bg"],
                fg=THEME["text_muted"]
            )

    def _randomize_traffic(self) -> None:
        """Randomize vehicle counts across all roads."""
        for r in ROADS:
            val = random.randint(3, 30)
            self.traffic.set_vehicle_count(r, val)
        self._sync_vehicles_with_counts()
        self._sync_hud()

    def _clear_emergencies(self) -> None:
        """Clear all active emergencies."""
        self.emergency.clear_all()
        self._sync_vehicles_with_counts()
        self._sync_hud()

    def _toggle_pause(self) -> None:
        """Pause or resume simulation."""
        is_running = self.controller.toggle_pause()
        self.pause_btn.configure(
            text="⏸ Pause Simulation" if is_running else "▶ Resume Simulation"
        )

    def _reset_simulation(self) -> None:
        """Reset simulation to initial clean state."""
        self.controller.reset()
        self.emergency.clear_all()
        self.traffic.reset(default_count=8)
        self.vehicles = {r: [] for r in ROADS}
        self.auto_flow_enabled = False
        self.auto_flow_btn.configure(
            text="🚗 Auto Traffic Flow: OFF",
            bg=THEME["btn_bg"],
            fg=THEME["text_muted"]
        )
        self._sync_vehicles_with_counts()
        self.pause_btn.configure(text="⏸ Pause Simulation")
        self._sync_hud()


def main() -> None:
    root = tk.Tk()
    app = SmartTrafficApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
