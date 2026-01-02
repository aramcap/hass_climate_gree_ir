"""Constants for the Gree AC IR integration."""

DOMAIN = "gree_ac_ir"
MANUFACTURER = "Gree"

# Configuration keys
CONF_BROADLINK_ENTITY = "broadlink_entity"

# Temperature
MIN_TEMP = 16
MAX_TEMP = 30
TEMP_STEP = 1

# Fan modes
FAN_MODE_AUTO = "auto"
FAN_MODE_MAX = "max"
FAN_MODE_MED = "med"
FAN_MODE_MIN = "min"

FAN_MODES = [FAN_MODE_AUTO, FAN_MODE_MAX, FAN_MODE_MED, FAN_MODE_MIN]

# Swing modes
SWING_MODE_OFF = "off"
SWING_MODE_VERTICAL = "vertical"
SWING_MODE_HORIZONTAL = "horizontal"
SWING_MODE_BOTH = "both"

SWING_MODES = [SWING_MODE_OFF, SWING_MODE_VERTICAL, SWING_MODE_HORIZONTAL, SWING_MODE_BOTH]

# Gree protocol encoding - Mode mapping
GREE_MODES = {
    "heat": 0x00,
    "cool": 0x02,
    "dry": 0x03,
    "fan_only": 0x04,
    "auto": 0x05,
}

# Gree protocol encoding - Fan speed mapping
GREE_FAN_MODES = {
    FAN_MODE_AUTO: 0b00,
    FAN_MODE_MAX: 0b01,
    FAN_MODE_MED: 0b10,
    FAN_MODE_MIN: 0b11,
}
