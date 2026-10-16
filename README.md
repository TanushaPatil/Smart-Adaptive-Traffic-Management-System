# Smart Adaptive Traffic Management System

A four-way traffic intersection simulator using **Python 3** and **Tkinter**. Dynamically adjusts green-light duration according to traffic density and prioritizes emergency vehicles.

---

## How to Run

From your terminal in the project directory, run:

```bash
python smart_traffic/main.py
```

or:

```bash
python smart_traffic_system.py
```

> **Requirements:** Python 3.8+ (standard library only; no external packages needed).

---

## Project Structure

```
smart_traffic/
    __init__.py
    traffic_logic.py       # Density calculation, green timing formula, fair scheduling
    emergency.py           # Emergency vehicle preemption & deterministic priority
    signal_controller.py   # State machine (ALL_RED -> GREEN -> YELLOW -> ALL_RED)
    main.py                # Tkinter GUI dashboard and controls
    README.md
```

---

## Key Features

1. **Left-Hand Traffic (LHT) Standard**:
   - Vehicles drive on the **left side** of two-way roads (standard in India, UK, Australia, Japan).
   - Stop lines, pedestrian zebra crossings, and directional lane arrows align strictly with incoming left-side approaches.
   - Primary signals are mounted on the driver's approaching left kerb.

2. **Realistic 3-Aspect Traffic Signals**:
   - 3 distinct lamps: Red (top), Amber (middle), Green (bottom).
   - High-contrast unlit lens vs. vivid illuminated active lamp with outer glow halo.
   - Road indicator badge above each signal post.

3. **Direction-Aware Vehicle Models**:
   - Direction-aligned windshields, forward-facing headlights, and rear brake lights.
   - Dual-pulse emergency sirens with alternating red and blue LED strobes.
   - Smooth queue progression: waiting cars advance towards the stop line without teleportation or count desynchronization.

4. **Adaptive Green Duration (`traffic_logic.py`)**:
   - Vehicle counts: 0 to 40 per road.
   - Dynamic green time: **5 seconds** (minimum) to **25 seconds** (maximum).
   - Traffic Density:
     - `LOW`: 0–12 vehicles
     - `MEDIUM`: 13–26 vehicles
     - `HIGH`: 27–40 vehicles
   - Fairness: Unserved roads accumulate waiting turns to prevent starvation.

5. **Emergency Vehicle Priority (`emergency.py`)**:
   - Toggle the emergency button on any road to prioritize it.
   - Safely curtails active conflicting green signal without conflicting green lights.
   - Deterministic rule if multiple emergencies exist: First-come-first-served (FIFO), with traffic volume as tie-breaker.
   - Automatically cleared when served.

6. **Signal State Machine (`signal_controller.py`)**:
   - Phases: `ALL_RED (1s)` $\rightarrow$ `GREEN (5–25s)` $\rightarrow$ `YELLOW (2s)` $\rightarrow$ `ALL_RED (1s)`.
   - Exactly one road receives GREEN at a time.
   - All conflicting roads remain RED.
   - Non-blocking updates using Tkinter `after()`.

7. **Interactive Dashboard & Analytics (`main.py`)**:
   - **Live Analytics HUD**: Real-time counter for total vehicles cleared, average delay turns, and starvation status.
   - **Auto Traffic Flow**: Continuous inbound traffic generator for autonomous testing.
   - **Traffic Adjusters**: Manual [-] and [+] count adjusters per road.
   - **Randomize Traffic**: Generates random vehicle numbers for testing.
   - **Clear Emergency Requests**: Clears all active emergencies.
   - **Pause / Resume**: Freezes countdown timer without duplicate callbacks.
   - **Reset Simulation**: Returns system to initial ALL_RED state.
