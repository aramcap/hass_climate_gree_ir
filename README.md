# Gree AC IR - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/aramcap/hass_climate_gree_ir.svg)](https://github.com/aramcap/hass_climate_gree_ir/releases)
[![License](https://img.shields.io/github/license/aramcap/hass_climate_gree_ir.svg)](LICENSE)

Control your Gree air conditioner via IR using an **existing Broadlink integration** in Home Assistant.

## 📋 Table of Contents

- [How it Works](#how-it-works)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Automations](#automations)
- [Lovelace Cards](#lovelace-cards)
- [Supported Models](#supported-models)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## How it Works

This integration creates a **climate entity** that:
1. Builds the IR command based on the Gree protocol (temperature, mode, fan, swing)
2. Sends the command through your existing Broadlink remote entity using `remote.send_command`
3. **Sends an OFF command to all devices on startup** to ensure a known initial state

**No direct connection to Broadlink devices** - it uses the Broadlink integration already configured in Home Assistant.

## Features

- ✅ Temperature control (16-30°C)
- ✅ HVAC modes (Heat, Cool, Dry, Fan Only, Auto, Off)
- ✅ Fan speed control (Auto, Max, Med, Min)
- ✅ Swing control (Vertical, Horizontal, Both, Off) - Optional
- ✅ Turn On/Off support
- ✅ UI Configuration (Config Flow)
- ✅ Multi-language support (English, Spanish)
- ✅ Uses existing Broadlink integration (RM3/RM4/Mini)
- ✅ Initial OFF command on startup

## Requirements

- Home Assistant 2025.12.0 or newer
- **Broadlink integration already configured** with your RM device
- Gree-compatible air conditioner

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/aramcap/hass_climate_gree_ir`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Gree AC IR"
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/aramcap/hass_climate_gree_ir/releases)
2. Extract the `custom_components/gree_ac_ir` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

Your directory structure should look like this:
```
config/
└── custom_components/
    └── gree_ac_ir/
        ├── __init__.py
        ├── climate.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── strings.json
        └── translations/
            ├── en.json
            └── es.json
```

## Configuration

### Prerequisites

Make sure you have the **Broadlink integration** configured in Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Add the Broadlink integration if not already configured
3. Your Broadlink RM device should appear as a remote entity (e.g., `remote.rm4c_mini`)

### Adding Gree AC IR

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Gree AC IR"
4. Select your Broadlink remote entity from the dropdown
5. Optionally, provide a custom name for the AC
6. Enable swing support if your AC supports it
7. Click **Submit**

### Configuration Options

| Option | Description | Required |
|--------|-------------|----------|
| Broadlink Remote Entity | The remote entity from Broadlink integration | Yes |
| Name | Custom name for the AC entity | No (default: "Gree AC") |
| Swing Support | Enable swing mode control | No (default: disabled) |

## Usage

After configuration, a new climate entity will be created. You can control it from:

- **Lovelace UI**: Use the thermostat card
- **Automations**: Create automations based on temperature, time, etc.
- **Scripts**: Include AC control in your scripts
- **Voice assistants**: Control via Google Home, Alexa, etc.

### Basic Thermostat Card

```yaml
type: thermostat
entity: climate.gree_ac
```

### Multi-AC Dashboard

```yaml
type: grid
cards:
  - type: thermostat
    entity: climate.dormitorio_ac
  - type: thermostat
    entity: climate.salon_ac
  - type: thermostat
    entity: climate.cocina_ac
```

## Automations

### Turn on AC at Specific Temperature by Schedule

```yaml
automation:
  - alias: "AC Bedroom - Night at 24°C"
    triggers:
      - trigger: time
        at: "22:00:00"
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.dormitorio_ac
        data:
          temperature: 24
          hvac_mode: cool
      - action: climate.set_fan_mode
        target:
          entity_id: climate.dormitorio_ac
        data:
          fan_mode: auto
```

### Turn off AC at Fixed Time

```yaml
  - alias: "AC Bedroom - Turn Off"
    triggers:
      - trigger: time
        at: "08:00:00"
    actions:
      - action: climate.turn_off
        target:
          entity_id: climate.dormitorio_ac
```

### Automatic AC Based on Temperature

```yaml
  - alias: "AC Living Room - Auto by temperature"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.living_room_temperature
        above: 26
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.salon_ac
        data:
          temperature: 24
          hvac_mode: cool
```

### Control Temperature with Input Number Slider

First, add this helper to `configuration.yaml`:

```yaml
input_number:
  dormitorio_temp:
    name: "Bedroom Temperature"
    min: 16
    max: 30
    step: 1
    unit_of_measurement: "°C"
```

Then create the automation:

```yaml
automation:
  - alias: "AC Bedroom - Temp from slider"
    triggers:
      - trigger: state
        entity_id: input_number.dormitorio_temp
    actions:
      - action: climate.set_temperature
        target:
          entity_id: climate.dormitorio_ac
        data:
          temperature: "{{ states('input_number.dormitorio_temp') | int }}"
```

## Lovelace Cards

### Advanced Control Panel

```yaml
type: vertical-stack
cards:
  - type: heading
    heading: "Air Conditioner Control"
  
  - type: grid
    columns: 3
    cards:
      - type: thermostat
        entity: climate.dormitorio_ac
      - type: thermostat
        entity: climate.salon_ac
      - type: thermostat
        entity: climate.cocina_ac
  
  - type: entities
    entities:
      - input_number.dormitorio_temp
      - climate.dormitorio_ac
    title: "Bedroom Details"
```

## Supported Models

This integration should work with air conditioners that use the **Gree YAC1FB IR protocol**, including:

- Gree
- Daitsu
- Tosot
- And other Gree-compatible brands

## Troubleshooting

### Broadlink Entity Not Found

Make sure the Broadlink integration is properly configured and your remote entity is available in Home Assistant.

### AC Not Responding

1. Point the Broadlink device toward the AC's IR receiver
2. Ensure there are no obstacles blocking the IR signal
3. Verify the AC uses Gree protocol (try with original remote first)
4. Check Home Assistant logs for error messages
5. Test with a manual command:

```yaml
action: remote.send_command
target:
  entity_id: remote.broadlink_rm
data:
  command: "b64:JgCSAAA..."
```

### Temperature Doesn't Update

**By design:** Infrared AC cannot confirm temperature (no feedback). The integration maintains internal state only.

**Solution:** Add an independent temperature sensor to your room and use it in automations.

### Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.gree_ac_ir: debug
```

Then check logs in **Settings → System → Logs**.

### Verify AC State

Go to **Developer Tools → States** and search for your climate entity to see the current state JSON.

### Installation Checklist

- [ ] Broadlink RM connected to WiFi with static IP
- [ ] Home Assistant 2025.12.0 or newer
- [ ] Broadlink integration configured in HA
- [ ] Files in `/config/custom_components/gree_ac_ir/`
- [ ] Home Assistant restarted after installation
- [ ] Integration added via UI
- [ ] Climate entity appears in Devices & Services
- [ ] Test: Change temperature from HA
- [ ] Check logs for errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please [open an issue](https://github.com/aramcap/hass_climate_gree_ir/issues) on GitHub.
