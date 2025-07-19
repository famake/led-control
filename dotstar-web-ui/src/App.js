import React, { useState, useEffect } from "react";
import { HexColorPicker } from "react-colorful";
import axios from "axios";
import "./App.css";

const API_URL = "http://192.168.1.46:5000";

const defaultRanges = {
  "Shelf Top": { from: 0, to: 108 },
  "Shelf Left": { from: 109, to: 130 },
  "Shelf Right": { from: 131, to: 152 },
};

const groupLabels = ["Shelf Top", "Shelf Left", "Shelf Right","Photon Ring"];

const App = () => {
  // Global States
  const [selectedGroups, setSelectedGroups] = useState([]);
  const [color, setColor] = useState("#ffffff");
  const [effect, setEffect] = useState("color_cycle");
  // Speed slider: range 0.1 to 1.0 sec; recommended for candle effects around 0.1-0.2 sec.
  const [speedSlider, setSpeedSlider] = useState(0.2);
  const effectiveSpeed = speedSlider.toFixed(2);

  // Effect-specific controls
  const [vibrancy, setVibrancy] = useState(255);
  const [pulsateMin, setPulsateMin] = useState(50);
  const [pulsateMax, setPulsateMax] = useState(255);
  // Candle intensity: 0.7 to 2.0 (default 1.0)
  const [candleIntensity, setCandleIntensity] = useState(1.0);
  // Candle base color (default warm yellow–orange)
  const [candleBase, setCandleBase] = useState("#ff9329");
  // New parameters for candle_gradient effect
  const [gradientAmplitude, setGradientAmplitude] = useState(0.5);
  const [gradientSpeed, setGradientSpeed] = useState(0.5);

  // Effects options (including the new candle_gradient effect)
  const effects = [
    "color_cycle",
    "pulsate",
    "starry_night",
    "candle",
    "candle_v2",        // If you want to keep the previous experimental v2
    "candle_gradient",  // Our new gradient-based candle effect
    "snake",
    "strobe",
    "gradient_wave",
    "favorite_cycle",
    "favorite_jump"
  ];

  // Collapsible sections
  const [showPower, setShowPower] = useState(true);
  const [showSolid, setShowSolid] = useState(true);
  const [showEffects, setShowEffects] = useState(true);
  const [showGroupConfig, setShowGroupConfig] = useState(true);

  // Group Range configuration (remembered in localStorage)
  const [groupRanges, setGroupRanges] = useState(() => {
    const saved = localStorage.getItem("groupRanges");
    return saved
      ? JSON.parse(saved)
      : {
          "Shelf Top": { ...defaultRanges["Shelf Top"] },
          "Shelf Left": { ...defaultRanges["Shelf Left"] },
          "Shelf Right": { ...defaultRanges["Shelf Right"] },
        };
  });
  const [groupRangeMessages, setGroupRangeMessages] = useState({
    "Shelf Top": "",
    "Shelf Left": "",
    "Shelf Right": "",
  });

  // Favorites integrated in Solid Color panel
  const [favoritesList, setFavoritesList] = useState([]);

  // Helper: convert hex string to RGB array
  const hexToRgb = (hex) => {
    const bigint = parseInt(hex.substring(1), 16);
    return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const res = await axios.get(`${API_URL}/favorites`);
      setFavoritesList(res.data);
    } catch (error) {
      console.error("Error fetching favorites:", error);
    }
  };

  const updateFavoritesOnServer = async (updatedFavorites) => {
    try {
      await axios.post(`${API_URL}/favorites`, updatedFavorites);
      setFavoritesList(updatedFavorites);
    } catch (error) {
      console.error("Error updating favorites:", error);
    }
  };

  const addFavorite = async () => {
    const rgb = hexToRgb(color);
    const updatedFavorites = [...favoritesList, rgb];
    updateFavoritesOnServer(updatedFavorites);
  };

  const removeFavorite = (index) => {
    const updatedFavorites = favoritesList.filter((_, i) => i !== index);
    updateFavoritesOnServer(updatedFavorites);
  };

  // When a favorite is clicked, update the main color picker.
  const selectFavorite = (favRgb) => {
    const hex =
      "#" +
      favRgb
        .map((val) => {
          const h = val.toString(16);
          return h.length === 1 ? "0" + h : h;
        })
        .join("");
    setColor(hex);
  };

  // Save groupRanges to localStorage on change
  useEffect(() => {
    localStorage.setItem("groupRanges", JSON.stringify(groupRanges));
  }, [groupRanges]);

  const handleGroupSelect = (groupLabel) => {
    setSelectedGroups((prev) =>
      prev.includes(groupLabel)
        ? prev.filter((g) => g !== groupLabel)
        : [...prev, groupLabel]
    );
  };

  const sendColor = async () => {
    if (selectedGroups.length === 0) return;
    const rgbColor = hexToRgb(color);
    try {
      await axios.post(`${API_URL}/set_color`, {
        groups: selectedGroups.map((label) => groupLabelToGroup(label)),
        color: rgbColor,
      });
    } catch (error) {
      console.error("Error setting color:", error);
    }
  };

  const startEffect = async () => {
    if (selectedGroups.length === 0) return;
    const data = {
      groups: selectedGroups.map((label) => groupLabelToGroup(label)),
      effect,
      speed: effectiveSpeed,
    };
    if (effect === "color_cycle") data.vibrancy = vibrancy;
    if (effect === "pulsate") {
      data.pulsate_min = pulsateMin;
      data.pulsate_max = pulsateMax;
    }
    if (effect === "candle") {
      data.intensity = candleIntensity;
      data.candle_base_color = hexToRgb(candleBase);
    }
    if (effect === "candle_v2") {
      data.intensity = candleIntensity;
      data.candle_base_color = hexToRgb(candleBase);
    }
    if (effect === "candle_gradient") {
      data.intensity = candleIntensity;
      data.candle_base_color = hexToRgb(candleBase);
      data.gradient_amplitude = gradientAmplitude;
      data.gradient_speed = gradientSpeed;
    }
    try {
      await axios.post(`${API_URL}/start_effect`, data);
    } catch (error) {
      console.error("Error starting effect:", error);
    }
  };

  const turnOffEffects = async () => {
    if (selectedGroups.length === 0) return;
    try {
      await axios.post(`${API_URL}/off`, {
        groups: selectedGroups.map((label) => groupLabelToGroup(label)),
      });
    } catch (error) {
      console.error("Error turning off effects:", error);
    }
  };

  const turnOffAll = async () => {
    try {
      await axios.post(`${API_URL}/off_all`);
    } catch (error) {
      console.error("Error turning off all LEDs:", error);
    }
  };

  const updateGroupRange = async (groupLabel) => {
    const range = groupRanges[groupLabel] || defaultRanges[groupLabel];
    if (range.from === "" || range.to === "") {
      setGroupRangeMessages((prev) => ({
        ...prev,
        [groupLabel]: "Please enter both start and end values.",
      }));
      return;
    }
    try {
      const response = await axios.post(`${API_URL}/update_group_range`, {
        group: groupLabelToGroup(groupLabel),
        start: parseInt(range.from),
        end: parseInt(range.to),
      });
      setGroupRangeMessages((prev) => ({
        ...prev,
        [groupLabel]: `Updated ${groupLabel}: ${response.data.range[0]} - ${response.data.range[1]}`,
      }));
    } catch (error) {
      console.error("Error updating group range:", error);
      setGroupRangeMessages((prev) => ({
        ...prev,
        [groupLabel]: "Error updating group range.",
      }));
    }
  };

  const handleRangeChange = (groupLabel, field, value) => {
    setGroupRanges((prev) => ({
      ...prev,
      [groupLabel]: {
        ...prev[groupLabel],
        [field]: value,
      },
    }));
  };

  // Helper: map display label to backend group key
  const groupLabelToGroup = (label) => {
    if (label === "Shelf Top") return "group1";
    if (label === "Shelf Left") return "group2";
    if (label === "Shelf Right") return "group3";
    if (label === "Photon Ring") return "photon_ring";
    return label;
  };

  // Collapsible section toggle helper
  const toggleSection = (current, setFn) => setFn(!current);

  return (
    <div className="container">
      <h1 className="title">LED Control Panel</h1>

      {/* Power Control Section */}
      <div className="card collapsible">
        <div className="card-header" onClick={() => toggleSection(showPower, setShowPower)}>
          <h2>Power Control {showPower ? "▼" : "►"}</h2>
        </div>
        {showPower && (
          <div className="card-content">
            <button className="action-button red" onClick={turnOffAll}>
              Turn Off All (Effects & Solid Colors)
            </button>
          </div>
        )}
      </div>

      {/* LED Groups Section */}
      <div className="card collapsible">
        <div className="card-header" onClick={() => toggleSection(showSolid, setShowSolid)}>
          <h2>LED Groups {showSolid ? "▼" : "►"}</h2>
        </div>
        {showSolid && (
          <div className="card-content">
            <div className="group-container">
              {groupLabels.map((label) => (
                <button
                  key={label}
                  onClick={() => handleGroupSelect(label)}
                  className={`group-button ${selectedGroups.includes(label) ? "selected" : ""}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Solid Color & Favorites Section */}
      <div className="card collapsible">
        <div className="card-header" onClick={() => toggleSection(showSolid, setShowSolid)}>
          <h2>Solid Color & Favorites {showSolid ? "▼" : "►"}</h2>
        </div>
        {showSolid && (
          <div className="card-content">
            <div className="color-picker-container">
              <HexColorPicker color={color} onChange={setColor} />
              <div className="color-preview" style={{ backgroundColor: color }}></div>
            </div>
            <button className="action-button" onClick={sendColor}>
              Set Solid Color
            </button>
            <div className="favorites-section">
              <h3>Favorites</h3>
              <div className="favorites-container">
                {favoritesList.map((fav, index) => {
                  const hex =
                    "#" +
                    fav
                      .map((val) => {
                        const h = val.toString(16);
                        return h.length === 1 ? "0" + h : h;
                      })
                      .join("");
                  return (
                    <div key={index} className="favorite-item">
                      <div
                        className="favorite-color"
                        style={{ backgroundColor: hex }}
                        onClick={() => selectFavorite(fav)}
                      ></div>
                      <button className="remove-button" onClick={() => removeFavorite(index)}>
                        X
                      </button>
                    </div>
                  );
                })}
              </div>
              <button className="action-button" onClick={addFavorite}>
                Add Current Color to Favorites
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Effects Section */}
      <div className="card collapsible">
        <div className="card-header" onClick={() => toggleSection(showEffects, setShowEffects)}>
          <h2>Effects {showEffects ? "▼" : "►"}</h2>
        </div>
        {showEffects && (
          <div className="card-content">
            <div className="effect-config">
              <label className="effect-label" htmlFor="effectSelect">
                Select Effect:
              </label>
              <select
                id="effectSelect"
                className="select"
                value={effect}
                onChange={(e) => setEffect(e.target.value)}
              >
                {effects.map((eff) => (
                  <option key={eff} value={eff}>
                    {eff.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="slider-container">
              <label htmlFor="speedRange">
                Speed: {effectiveSpeed} sec (lower = faster, higher = slower)
              </label>
              <input
                id="speedRange"
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={speedSlider}
                onChange={(e) => setSpeedSlider(parseFloat(e.target.value))}
              />
            </div>
            {effect === "color_cycle" && (
              <div className="slider-container">
                <label htmlFor="vibrancyRange">Vibrancy: {vibrancy}</label>
                <input
                  id="vibrancyRange"
                  type="range"
                  min="0"
                  max="255"
                  value={vibrancy}
                  onChange={(e) => setVibrancy(parseInt(e.target.value))}
                />
              </div>
            )}
            {effect === "pulsate" && (
              <>
                <div className="slider-container">
                  <label htmlFor="pulsateMinRange">Pulsate Min: {pulsateMin}</label>
                  <input
                    id="pulsateMinRange"
                    type="range"
                    min="0"
                    max="255"
                    value={pulsateMin}
                    onChange={(e) => setPulsateMin(parseInt(e.target.value))}
                  />
                </div>
                <div className="slider-container">
                  <label htmlFor="pulsateMaxRange">Pulsate Max: {pulsateMax}</label>
                  <input
                    id="pulsateMaxRange"
                    type="range"
                    min="0"
                    max="255"
                    value={pulsateMax}
                    onChange={(e) => setPulsateMax(parseInt(e.target.value))}
                  />
                </div>
              </>
            )}
            {(effect === "candle" || effect === "candle_v2") && (
              <>
                <div className="slider-container">
                  <label htmlFor="candleIntensity">Candle Intensity: {candleIntensity.toFixed(2)}</label>
                  <input
                    id="candleIntensity"
                    type="range"
                    min="0.7"
                    max="2.0"
                    step="0.05"
                    value={candleIntensity}
                    onChange={(e) => setCandleIntensity(parseFloat(e.target.value))}
                  />
                </div>
                <div className="slider-container">
                  <label className="effect-label" htmlFor="candleBase">
                    Candle Base Color:
                  </label>
                  <HexColorPicker color={candleBase} onChange={setCandleBase} />
                  <div className="color-preview" style={{ backgroundColor: candleBase }}></div>
                </div>
              </>
            )}
            {effect === "candle_gradient" && (
              <>
                <div className="slider-container">
                  <label htmlFor="candleIntensity">Candle Intensity: {candleIntensity.toFixed(2)}</label>
                  <input
                    id="candleIntensity"
                    type="range"
                    min="0.7"
                    max="2.0"
                    step="0.05"
                    value={candleIntensity}
                    onChange={(e) => setCandleIntensity(parseFloat(e.target.value))}
                  />
                </div>
                <div className="slider-container">
                  <label className="effect-label" htmlFor="candleBase">
                    Candle Base Color:
                  </label>
                  <HexColorPicker color={candleBase} onChange={setCandleBase} />
                  <div className="color-preview" style={{ backgroundColor: candleBase }}></div>
                </div>
                <div className="slider-container">
                  <label htmlFor="gradientAmplitude">Gradient Amplitude: {gradientAmplitude.toFixed(2)}</label>
                  <input
                    id="gradientAmplitude"
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={gradientAmplitude}
                    onChange={(e) => setGradientAmplitude(parseFloat(e.target.value))}
                  />
                </div>
                <div className="slider-container">
                  <label htmlFor="gradientSpeed">Gradient Speed: {gradientSpeed.toFixed(2)}</label>
                  <input
                    id="gradientSpeed"
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={gradientSpeed}
                    onChange={(e) => setGradientSpeed(parseFloat(e.target.value))}
                  />
                </div>
              </>
            )}
            <div className="button-group">
              <button className="action-button" onClick={startEffect}>
                Start Effect
              </button>
              <button className="action-button" onClick={turnOffEffects}>
                Turn Off Effects
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Group Range Configuration Section */}
      <div className="card collapsible">
        <div className="card-header" onClick={() => toggleSection(showGroupConfig, setShowGroupConfig)}>
          <h2>Group Range Configuration {showGroupConfig ? "▼" : "►"}</h2>
        </div>
        {showGroupConfig && (
          <div className="card-content">
            {groupLabels.map((label) => {
  if (label === "Photon Ring") return null; // skip visning av range-editor

  const range = groupRanges[label] || defaultRanges[label];
  return (
    <div key={label} className="group-range-config">
      <h3>{label}</h3>
      <div className="range-inputs">
        <label>From LED:</label>
        <input
          type="number"
          min={defaultRanges[label].from}
          max={range.to}
          value={range.from}
          onChange={(e) => handleRangeChange(label, "from", e.target.value)}
          className="input-field"
        />
        <label>To LED:</label>
        <input
          type="number"
          min={range.from}
          max={defaultRanges[label].to}
          value={range.to}
          onChange={(e) => handleRangeChange(label, "to", e.target.value)}
          className="input-field"
        />
      </div>
      <button className="action-button" onClick={() => updateGroupRange(label)}>
        Update {label} Range
      </button>
      {groupRangeMessages[label] && (
        <div className="message">{groupRangeMessages[label]}</div>
      )}
    </div>
  );
})}

          </div>
        )}
      </div>
    </div>
  );
};

export default App;

