# Streamlit Dashboard

This document explains how to launch a simple Streamlit dashboard for inspecting a generated PyAurora 4X game state.

The dashboard displays star systems, sample ships and empire information using tabs. It relies on the `streamlit_dashboard.py` script at the project root which builds a small game using `GameSimulation`.

## Running the Dashboard

1. Install the required package:

```bash
pip install streamlit
```

2. Run the application from the repository root:

```bash
streamlit run streamlit_dashboard.py
```

The dashboard will open in your browser. Use the sidebar to switch between Worlds, Ships and Empires views.

