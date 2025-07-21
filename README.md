# Raspberry Pi LED Controller

This repository contains a small Flask backend and a React based web interface
for controlling LED strips over the network. The backend script `app.py`
exposes several REST endpoints for setting colors, running effects and managing
LED groups. LED data is transmitted to other devices using the Art-Net
protocol. A list of target devices with IP address, Art-Net universe and pixel
count is stored in `devices.json`.

The web client lives in `dotstar-web-ui` and was bootstrapped with
Create React App.

The code for Particle Photon lives in `photon`.

## Requirements

- Python 3 with the packages listed in `requirements.txt`
- Node.js and npm for the web UI

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

