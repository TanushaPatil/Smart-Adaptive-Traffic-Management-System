## 👥 Project Team

**Developed by:**

- **Sarvesh Pillai** — [GitHub Profile](https://github.com/PillaiSarveshX03)
- **Tanvee Patil** — [GitHub Profile](https://github.com/patiltanvee)
- **Tanusha Patil** — [GitHub Profile](https://github.com/TanushaPatil)

---

# 🚦 Smart Adaptive Traffic Management System

A four-way traffic intersection simulator built using **Python 3 and Tkinter**. The system dynamically adjusts green-light duration according to traffic density and prioritizes emergency vehicles while maintaining safe signal transitions.

---

## ✨ Key Features

- 🚗 Four-way traffic simulation: North, South, East, and West.
- 🚦 Three-aspect traffic signals: Red, Amber, and Green.
- 🧠 Adaptive green-light timing based on vehicle count.
- 🚑 Emergency vehicle priority.
- ⚖️ Fair scheduling to reduce excessive waiting.
- 📊 Interactive dashboard with traffic statistics.
- ⏱️ Non-blocking updates using Tkinter's `after()` method.

## 🛠️ Technologies Used

- Python 3
- Tkinter
- Python Standard Library
- `unittest` for automated testing

## 💻 How to Run

**Requirements:** Python 3.8 or newer.

Run from the project root directory:

```bash
python smart_traffic/main.py
```

On Windows, you can also use:

```bash
py smart_traffic/main.py
```

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
└── tests/
    └── test_traffic_system.py
```

## 🔄 System Workflow

1. Initialize the traffic logic, emergency manager, signal controller, and GUI.
2. Generate or adjust vehicle counts for each road.
3. Classify traffic density as LOW, MEDIUM, or HIGH.
4. Calculate green-light duration according to traffic demand.
5. Select the next road using traffic volume, waiting turns, and emergency requests.
6. Transition through the appropriate traffic-signal phases.
7. Update the dashboard and statistics.
8. Continue until the simulation is paused or reset.

## 🧪 Run Tests

```bash
python -m unittest discover -s tests -v
```

## ⚠️ Scope and Limitations

This project is an educational desktop simulation. Vehicle counts are simulated, and the application is not connected to real traffic cameras, road sensors, GPS, or physical traffic lights. Real-world deployment would require extensive safety validation and testing.

## 🚀 Future Enhancements

- Camera-based vehicle detection and IoT sensor integration.
- Pedestrian signals and crossing-demand handling.
- Traffic history storage and analytics.
- Testing with real-world traffic datasets.
- Improved vehicle animation and collision testing.

## 🎯 Conclusion

The Smart Adaptive Traffic Management System demonstrates adaptive signal timing, traffic-density classification, fair road scheduling, and emergency vehicle prioritization using Python and Tkinter. Its modular design supports learning, testing, and future enhancements.

## 📚 References

- [Python Documentation](https://docs.python.org/3/)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
