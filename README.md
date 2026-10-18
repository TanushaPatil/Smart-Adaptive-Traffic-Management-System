# 🚦 Smart Adaptive Traffic Management System

A four-way traffic intersection simulator built using **Python 3 and Tkinter**. The system dynamically adjusts green-light duration according to traffic density, schedules roads fairly, and prioritizes emergency vehicles while maintaining safe signal transitions.

## 📌 Project Overview

Traditional fixed-time traffic signals allocate a predefined amount of time to each road, even when traffic density varies. This project demonstrates an adaptive approach in which simulated vehicle counts help determine green-light duration.

The application provides a graphical dashboard to visualize traffic across four directions: **North, South, East, and West**.

## ✨ Key Features

### 1. 🚗 Four-Way Traffic Simulation
- Simulates traffic on North, South, East, and West roads.
- Supports vehicle-count adjustment and random traffic generation.
- Includes automatic traffic-flow simulation.

### 2. 🚦 Realistic Traffic Signals
- Three-aspect signals: Red, Amber, and Green.
- Uses the signal phases `ALL_RED`, `GREEN`, and `YELLOW`.
- Allows only one road to receive a green signal at a time.
- Uses an all-red clearance interval between conflicting green phases.

### 3. 🧠 Adaptive Green-Light Timing
- Calculates green-light duration based on vehicle count.
- Minimum green duration: **5 seconds**.
- Maximum green duration: **25 seconds**.
- Classifies traffic as LOW, MEDIUM, or HIGH.

| Vehicle Count | Traffic Density |
|---|---|
| 0–12 | LOW |
| 13–26 | MEDIUM |
| 27–40 | HIGH |

The green-light duration is calculated using:

`duration = 5 + round((vehicle_count / 40) * 20)`

The result is limited to the range of 5–25 seconds.

### 4. 🚑 Emergency Vehicle Priority
- Allows emergency requests to be created for any road.
- Prioritizes emergency requests according to the implemented selection rules.
- Supports first-come-first-served ordering, with traffic volume used as a tie-breaker where applicable.
- Maintains yellow and all-red clearance phases when changing signals.

### 5. ⚖️ Fair Road Scheduling
- Considers traffic volume and waiting turns when selecting the next road.
- Helps prevent a road from waiting indefinitely while other roads repeatedly receive green signals.

### 6. 📊 Interactive Dashboard
- Displays vehicle counts and traffic conditions.
- Tracks cleared vehicles and waiting information.
- Provides traffic count adjustment controls.
- Supports random traffic generation.
- Includes emergency request controls.
- Provides Pause, Resume, and Reset functionality.

### 7. ⏱️ Non-Blocking Updates
Uses Tkinter's `after()` method to update the countdown and simulation periodically without blocking the graphical interface.

## 🛠️ Technologies Used

- **Python 3** — core application logic
- **Tkinter** — graphical user interface
- **Python Standard Library** — supporting functionality
- **unittest** — automated testing of selected behaviours

No third-party Python packages are required according to the project setup.

## 📁 Project Structure

```text
SMAER/
├── smart_traffic/
│   ├── __init__.py
│   ├── traffic_logic.py
│   ├── emergency.py
│   ├── signal_controller.py
│   ├── main.py
│   └── README.md
│
└── tests/
    └── test_traffic_system.py
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Tkinter dashboard, controls, and visual simulation |
| `traffic_logic.py` | Traffic density, green-time calculation, and fair scheduling |
| `emergency.py` | Emergency request management and priority selection |
| `signal_controller.py` | Signal phases, countdown, pause/resume, and reset |
| `__init__.py` | Package-level imports and exports |
| `test_traffic_system.py` | Automated tests for selected system behaviours |

## 💻 Installation and Execution

### Prerequisites

- Python **3.8 or newer**
- Git (optional, for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
```

Replace `<YOUR_REPOSITORY_URL>` with your actual GitHub repository URL.

### Step 2: Open the Project Directory

```bash
cd <YOUR_PROJECT_FOLDER>
```

Open the folder containing the `smart_traffic` and `tests` directories.

### Step 3: Run the Application

```bash
python smart_traffic/main.py
```

On Windows, you can also try:

```bash
py smart_traffic/main.py
```

### Step 4: Run the Tests

```bash
python -m unittest discover -s tests -v
```

Run the tests from the project root directory.

## 🔄 System Workflow

1. The application initializes the traffic logic, emergency manager, signal controller, and GUI.
2. Vehicle counts are generated, randomized, or adjusted for each road.
3. The system classifies the traffic density for each road.
4. The adaptive timing algorithm calculates the green-light duration.
5. The controller selects a road based on traffic demand, waiting turns, and emergency requests.
6. The signal moves through the defined clearance and traffic-light phases.
7. The dashboard updates the timer, traffic information, and statistics.
8. The cycle continues until the simulation is paused or reset.

## 🧪 Testing Scenarios

The system can be tested using the following scenarios:

- **Low traffic:** Check the calculated green-light duration for a small vehicle count.
- **High traffic:** Check the response to larger vehicle counts.
- **Signal transitions:** Observe the GREEN, YELLOW, and ALL_RED phases.
- **Emergency priority:** Submit an emergency request and observe the controller's response.
- **Fair scheduling:** Observe how roads waiting for multiple turns are considered.
- **Pause and resume:** Verify that scheduled updates stop and continue appropriately.
- **Reset:** Confirm that the simulation returns to its initial state.

## ⚠️ Scope and Limitations

This project is a **simulation for educational and demonstration purposes**.

- Vehicle counts are simulated rather than collected from live roads.
- The application is not connected to real traffic cameras, IoT sensors, GPS, or physical traffic lights.
- Real-world deployment would require reliable live inputs, extensive testing, safety validation, and integration with authorized traffic-control infrastructure.

## 🚀 Future Enhancements

- Integrate camera-based vehicle detection or IoT traffic sensors.
- Add pedestrian signals and pedestrian-demand handling.
- Store traffic history and export analytics.
- Evaluate scheduling algorithms using real traffic datasets.
- Improve vehicle animation and collision testing.
- Introduce configurable timing and density thresholds.

## 🎯 Conclusion

The Smart Adaptive Traffic Management System demonstrates how adaptive timing, traffic-density classification, fair road scheduling, emergency priority, and signal-state management can be combined in a Python desktop application.

Its modular structure separates the user interface from traffic calculations and signal control, making the project easier to understand, test, and extend.

## 👥 Project Team

| Team Member | GitHub Profile |
|---|---|
| **Sarvesh Pillai** | [@PillaiSarveshX03](https://github.com/PillaiSarveshX03) |
| **Tanvi Patil** | [@patiltanvee](https://github.com/patiltanvee) |
| **Tanusha Patil** | [@TanushaPatil](https://github.com/TanushaPatil) |

## 📚 References

- [Python Documentation](https://docs.python.org/3/)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

---

*Developed as an academic project to demonstrate adaptive traffic-control concepts using Python.*
