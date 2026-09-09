# TRINETRA

**Threat Recognition & Intelligent Network for Enhanced Tracking and Response Automation**

TRINETRA is an AI-powered border surveillance prototype designed to demonstrate real-time person detection, tracking, restricted-zone monitoring, and intrusion alerting from a live camera or prerecorded surveillance footage.

## Overview

The prototype combines computer vision, object tracking, a web dashboard, and event logging into a single surveillance workflow.

A user selects a surveillance source, defines a restricted zone directly on the dashboard, and starts monitoring. When a tracked person enters the restricted area, the system identifies the person ID, records the intrusion, captures a snapshot, and updates the security-event panel.

## Features

- 🎥 **Live Camera Monitoring** — use a connected webcam as the surveillance source.
- 🎞️ **Demo Video Mode** — run the bundled prerecorded surveillance footage for demonstrations.
- 🤖 **Person Detection & Tracking** — uses YOLO for real-time person detection and tracking IDs.
- 📍 **Interactive Restricted Zone** — define a polygonal monitoring area directly from the web dashboard.
- 🚨 **Intrusion Detection** — detects when a tracked person enters the configured restricted zone.
- 🆔 **Person Identification** — displays tracking IDs for detected people and intrusion events.
- 📸 **Intrusion Snapshots** — automatically saves a frame when a new intrusion is detected.
- ⚡ **Live Event Updates** — the dashboard receives new intrusion events through Server-Sent Events (SSE).
- 🔄 **Source Switching** — switch between live camera and demo footage and configure a fresh zone for the selected source.

## System Architecture

```text
Camera / Demo Video
        ↓
   OpenCV Capture
        ↓
     YOLO Tracking
        ↓
  Restricted-Zone Check
        ↓
   Intrusion Detection
      ↙        ↘
Snapshot      events.json
    ↓              ↓
Express API    SSE Stream
      ↘          ↙
       React Dashboard
```

## Tech Stack

- **Python** — computer-vision and detection pipeline
- **YOLO (Ultralytics)** — person detection and tracking
- **OpenCV** — video capture, frame processing, and snapshots
- **Flask** — video streaming, zone configuration, source control, and event streaming
- **Flask-CORS** — cross-origin access for the frontend
- **Node.js / Express** — serves snapshots and the events API
- **React + Vite** — surveillance dashboard
- **JSON** — lightweight event storage for the prototype

## Project Structure

```text
Trinetra-Prototype/
├── main.py
├── yolo11n.pt
├── events.json
├── requirements.txt
├── footage/
│   └── borderTest.mp4
├── snapshots/
├── backend/
│   ├── server.js
│   └── package.json
└── frontend/
    ├── src/
    │   └── App.jsx
    ├── package.json
    └── ...
```

## How It Works

1. Start the Python computer-vision service.
2. Start the Express backend and React frontend.
3. Select **LIVE CAMERA** or **DEMO VIDEO** from the dashboard.
4. Click points on the surveillance feed to define the restricted zone.
5. Confirm the zone to begin detection.
6. YOLO tracks people in the selected source.
7. The system checks each person's bottom-center/feet point against the restricted polygon.
8. A new zone entry creates an intrusion event, saves a snapshot, and updates the dashboard.
9. Switching sources clears the previous zone so a new restricted area can be configured for the selected feed.

## Running the Prototype

### 1. Python environment

Create and activate a virtual environment, then install the dependencies:

```bash
pip install -r requirements.txt
```

Run the Python service:

```bash
python main.py
```

The Flask service runs on:

```text
http://localhost:5001
```

### 2. Express backend

From the `backend` directory:

```bash
npm install
node server.js
```

The Express server runs on:

```text
http://localhost:5000
```

### 3. React frontend

From the `frontend` directory:

```bash
npm install
npm run dev
```

Open the Vite development URL shown in the terminal.

## Notes

- The prototype processes video at a fixed **1280 × 720** working resolution.
- The bundled demo footage is intended for presentations and testing.
- `events.json` provides simple persistent event storage for the prototype.
- The project is designed as a demonstration of AI-assisted surveillance and should not be treated as a production-grade security system.

## Current Status

🚧 **Prototype / Hackathon Project**

TRINETRA currently demonstrates the core surveillance workflow: source selection, interactive zone configuration, person tracking, intrusion detection, snapshot capture, and live dashboard event updates.

## Author

**Sambhav**

Built as an AI/computer-vision prototype for hackathon demonstration and experimentation.
