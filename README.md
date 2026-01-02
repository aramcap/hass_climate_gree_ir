# Gree AC IR - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/aramcap/hass_climate_gree_ir.svg)](https://github.com/aramcap/hass_climate_gree_ir/releases)
[![License](https://img.shields.io/github/license/aramcap/hass_climate_gree_ir.svg)](LICENSE)

Control your Gree air conditioner via IR using a Broadlink RM device in Home Assistant.

## Features

- ✅ Temperature control (16-30°C)
- ✅ HVAC modes (Heat, Cool, Dry, Fan Only, Auto, Off)
- ✅ Fan speed control (Auto, Max, Med, Min)
- ✅ Swing control (Vertical, Horizontal, Both, Off)
- ✅ Turn On/Off support
- ✅ UI Configuration (Config Flow)
- ✅ Multi-language support (English, Spanish)
- ✅ Compatible with Broadlink RM3/RM4/Mini

## Requirements

- Home Assistant 2024.1.0 or newer
- Broadlink RM device (RM3, RM4, or Mini)
- Gree/Daitsu compatible air conditioner

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
2. Extract the `custom_components/gree_ac` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

Your directory structure should look like this:
```
config/
└── custom_components/
    └── gree_ac/
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

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Gree AC IR"
4. Enter the IP address of your Broadlink RM device
5. Optionally, provide a custom name for the AC
6. Click **Submit**

### Configuration Options

| Option | Description | Required |
|--------|-------------|----------|
| Host | IP address of your Broadlink RM device | Yes |
| Name | Custom name for the AC entity | No (default: "Gree AC") |

## Usage

After configuration, a new climate entity will be created. You can control it from:

- **Lovelace UI**: Use the thermostat card
- **Automations**: Create automations based on temperature, time, etc.
- **Scripts**: Include AC control in your scripts
- **Voice assistants**: Control via Google Home, Alexa, etc.

### Example Lovelace Card

```yaml
type: thermostat
entity: climate.gree_ac_192_168_1_100
```

### Example Automation

```yaml
automation:
  - alias: "Turn on AC when temperature is high"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_temperature
        above: 26
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.gree_ac_192_168_1_100
        data:
          temperature: 24
          hvac_mode: cool
```

## Supported Models

This integration should work with most Gree and Daitsu air conditioners that use the standard Gree IR protocol, including:

- Gree
- Daitsu
- Tosot
- And other Gree-compatible brands

## Troubleshooting

### Cannot connect to Broadlink device

1. Ensure the Broadlink device is powered on and connected to your network
2. Verify the IP address is correct
3. Check that the device is accessible from Home Assistant (ping test)
4. Make sure the Broadlink device is authenticated (use the Broadlink app first)

### AC not responding

1. Point the Broadlink device toward the AC's IR receiver
2. Ensure there are no obstacles blocking the IR signal
3. Check Home Assistant logs for error messages

### Logs

Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.gree_ac: debug
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please [open an issue](https://github.com/aramcap/hass_climate_gree_ir/issues) on GitHub.