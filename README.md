# Raspberry Pi LED Controller

This repository contains a small Flask backend and a React based web interface
for controlling LEDs. The backend script `app.py` exposes several REST
endpoints for setting colors, running effects and managing LED groups. LED data
is sent to other devices over the network using the Art-Net protocol. Device
definitions are stored in `devices.json` and can be managed through the API or a
future GUI.

The web client lives in `dotstar-web-ui` and was bootstrapped with
Create React App.

The code for Particle Photon lives in `photon`.

## Requirements

- Python 3 with the packages listed in `requirements.txt`
- Node.js and npm for the web UI
The controller no longer requires local SPI access.

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
Configured lighting devices are listed in `devices.json` and may be updated via
the `/devices` endpoint.

