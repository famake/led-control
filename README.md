# Raspberry Pi LED Controller

This repository contains a small Flask backend and a React based web interface
for controlling DotStar LED strips connected to a Raspberry Pi. The backend
script `app.py` exposes several REST endpoints for setting
colors, running effects and managing LED groups. It can also send color data to
a Particle Photon device by setting `PARTICLE_DEVICE_ID` and
`PARTICLE_ACCESS_TOKEN` in the script.

The web client lives in `dotstar-web-ui` and was bootstrapped with
Create React App.

## Requirements

- Python 3 with the packages listed in `requirements.txt`
- Node.js and npm for the web UI
- On the Raspberry Pi you also need the system package `python3-spidev` for SPI
  access

## Running

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the backend:
   ```bash
   python3 app.py
   ```
3. In a separate terminal, start the web UI:
   ```bash
   cd dotstar-web-ui
   npm install
   npm start
   ```
   The interface will be available at <http://localhost:3000> and communicates
   with the Flask server on port 5000.

Favorite colors are stored in `favorites.json` and can be managed via the UI.
LED group ranges may be updated with the `/update_group_range` endpoint.

