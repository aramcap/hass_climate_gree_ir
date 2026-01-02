"""Climate platform for Gree/Daitsu AC integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FAN_MODES,
    GREE_FAN_MODES,
    GREE_MODES,
    MANUFACTURER,
    MAX_TEMP,
    MIN_TEMP,
    SWING_MODES,
    TEMP_STEP,
)

_LOGGER = logging.getLogger(__name__)

HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.AUTO,
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree AC climate platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]

    entity = GreeACClimate(
        hass=hass,
        device=data["device"],
        name=data["name"],
        host=data["host"],
        entry_id=config_entry.entry_id,
    )
    async_add_entities([entity])


class GreeACClimate(ClimateEntity):
    """Represents a Gree/Daitsu air conditioner."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = HVAC_MODES
    _attr_fan_modes = FAN_MODES
    _attr_swing_modes = SWING_MODES

    def __init__(
        self,
        hass: HomeAssistant,
        device,
        name: str,
        host: str,
        entry_id: str,
    ) -> None:
        """Initialize the Gree AC climate entity."""
        self.hass = hass
        self._device = device
        self._host = host
        self._entry_id = entry_id

        # Entity attributes
        self._attr_unique_id = f"gree_ac_{host.replace('.', '_')}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name=name,
            manufacturer=MANUFACTURER,
            model="Air Conditioner",
            sw_version="1.0.0",
        )

        # AC state
        self._hvac_mode = HVACMode.OFF
        self._target_temperature = 24
        self._current_temperature: float | None = None
        self._fan_mode = "auto"
        self._swing_mode = "off"
        self._swing_vertical = False
        self._swing_horizontal = False

    @property
    def current_temperature(self) -> float | None:
        """Return current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self) -> int | None:
        """Return target temperature."""
        return self._target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        return self._hvac_mode

    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode."""
        return self._fan_mode

    @property
    def swing_mode(self) -> str | None:
        """Return current swing mode."""
        return self._swing_mode

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature is not None:
            self._target_temperature = int(
                max(self._attr_min_temp, min(self._attr_max_temp, temperature))
            )
            await self._send_command()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        self._hvac_mode = hvac_mode
        await self._send_command()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        if fan_mode in self._attr_fan_modes:
            self._fan_mode = fan_mode
            await self._send_command()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing mode."""
        if swing_mode in self._attr_swing_modes:
            self._swing_mode = swing_mode

            # Parse horizontal and vertical swing
            if swing_mode == "off":
                self._swing_vertical = False
                self._swing_horizontal = False
            elif swing_mode == "vertical":
                self._swing_vertical = True
                self._swing_horizontal = False
            elif swing_mode == "horizontal":
                self._swing_vertical = False
                self._swing_horizontal = True
            elif swing_mode == "both":
                self._swing_vertical = True
                self._swing_horizontal = True

            await self._send_command()

    async def async_turn_on(self) -> None:
        """Turn on."""
        if self._hvac_mode == HVACMode.OFF:
            self._hvac_mode = HVACMode.COOL
        await self._send_command()

    async def async_turn_off(self) -> None:
        """Turn off."""
        self._hvac_mode = HVACMode.OFF
        await self._send_command()

    async def _send_command(self) -> None:
        """Send IR command to Broadlink device."""
        try:
            # Build Gree command bytes
            gree_bytes = self._build_gree_command()

            _LOGGER.debug(
                "Gree command bytes: %s",
                " ".join(f"{b:02X}" for b in gree_bytes),
            )

            # Encode to IR timings and send to Broadlink
            ir_command = self._encode_ir_command(gree_bytes)

            _LOGGER.debug("Sending IR command (%d bytes)", len(ir_command))

            await self.hass.async_add_executor_job(
                self._device.send_data, ir_command
            )

            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error sending command: %s", err)

    def _encode_ir_command(self, gree_bytes: bytes) -> bytes:
        """Encode Gree command bytes to Broadlink IR format.

        Gree IR Protocol (YAC1FB protocol):
        - Carrier frequency: 38kHz
        - Header: 9000µs pulse + 4500µs space
        - Bit 0: 620µs pulse + 540µs space
        - Bit 1: 620µs pulse + 1650µs space
        - Message separator: 620µs pulse + 20000µs space
        - Footer: 620µs pulse

        The 8-byte command is sent as:
        - First 4 bytes + 3-bit fixed message separator
        - Last 4 bytes + checksum
        """
        # Gree IR timing constants (in microseconds)
        HEADER_PULSE = 9000
        HEADER_SPACE = 4500
        BIT_PULSE = 620
        BIT_ZERO_SPACE = 540
        BIT_ONE_SPACE = 1650
        MESSAGE_SPACE = 20000
        FOOTER_PULSE = 620

        # Broadlink frequency constant (for 38kHz)
        # Broadlink uses 269/8192 seconds as time unit ≈ 32.84µs
        BROADLINK_UNIT = 32.84

        timings: list[int] = []

        def add_pulse_space(pulse_us: int, space_us: int) -> None:
            """Add a pulse and space to timings."""
            timings.append(int(pulse_us / BROADLINK_UNIT))
            timings.append(int(space_us / BROADLINK_UNIT))

        def add_byte(byte: int) -> None:
            """Add a byte (8 bits, LSB first) to timings."""
            for _ in range(8):
                bit = byte & 1
                if bit:
                    add_pulse_space(BIT_PULSE, BIT_ONE_SPACE)
                else:
                    add_pulse_space(BIT_PULSE, BIT_ZERO_SPACE)
                byte >>= 1

        # Header
        add_pulse_space(HEADER_PULSE, HEADER_SPACE)

        # First 4 bytes
        for i in range(4):
            add_byte(gree_bytes[i])

        # Fixed 3-bit connector (value: 010 = 2, sent LSB first)
        add_pulse_space(BIT_PULSE, BIT_ZERO_SPACE)  # bit 0
        add_pulse_space(BIT_PULSE, BIT_ONE_SPACE)   # bit 1
        add_pulse_space(BIT_PULSE, BIT_ZERO_SPACE)  # bit 0

        # Message separator
        add_pulse_space(BIT_PULSE, MESSAGE_SPACE)

        # Second header (shorter)
        add_pulse_space(HEADER_PULSE, HEADER_SPACE)

        # Last 4 bytes
        for i in range(4, 8):
            add_byte(gree_bytes[i])

        # Footer pulse (just pulse, minimal space)
        timings.append(int(FOOTER_PULSE / BROADLINK_UNIT))

        # Convert to Broadlink format
        return self._timings_to_broadlink(timings)

    def _timings_to_broadlink(self, timings: list[int]) -> bytes:
        """Convert IR timings to Broadlink packet format.

        Broadlink format:
        - Byte 0: 0x26 (IR code identifier)
        - Byte 1: repeat count (0 = no repeat)
        - Bytes 2-3: length of timing data (little endian)
        - Remaining bytes: timing data
        - End marker: 0x0d, 0x05
        """
        # Build timing data
        timing_data = bytearray()

        for timing in timings:
            if timing > 255:
                # Extended format for values > 255
                timing_data.append(0x00)
                timing_data.append((timing >> 8) & 0xFF)
                timing_data.append(timing & 0xFF)
            else:
                timing_data.append(timing)

        # Build Broadlink packet
        packet = bytearray()
        packet.append(0x26)  # IR identifier
        packet.append(0x00)  # No repeat
        packet.append(len(timing_data) & 0xFF)  # Length low byte
        packet.append((len(timing_data) >> 8) & 0xFF)  # Length high byte
        packet.extend(timing_data)
        packet.append(0x0D)  # End marker
        packet.append(0x05)  # End marker

        # Pad to multiple of 16 bytes (Broadlink requirement)
        while len(packet) % 16 != 0:
            packet.append(0x00)

        return bytes(packet)

    def _build_gree_command(self) -> bytes:
        """Build Gree protocol 8-byte command."""
        # Byte 0: Power + Temperature
        power = 1 if self._hvac_mode != HVACMode.OFF else 0
        temp_bits = max(0, min(14, self._target_temperature - 16))
        byte0 = (power << 0) | (temp_bits << 2)

        # Byte 1: Timer (disabled)
        byte1 = 0x00

        # Byte 2: Standard config
        byte2 = 0x50

        # Byte 3: Mode + Swing Horizontal
        mode_value = self._hvac_mode.value if self._hvac_mode != HVACMode.OFF else "cool"
        mode_bits = GREE_MODES.get(mode_value, 0x02)
        swing_h_bits = 1 if self._swing_horizontal else 0
        byte3 = (mode_bits << 0) | (swing_h_bits << 4)

        # Byte 4: Swing Vertical + Fan Speed
        swing_v_bits = 1 if self._swing_vertical else 0
        fan_bits = GREE_FAN_MODES.get(self._fan_mode, 0b00)
        byte4 = (swing_v_bits << 0) | (fan_bits << 4)

        # Byte 5: Display temp
        byte5 = 0x00

        # Byte 6: Reserved
        byte6 = 0x00

        # Byte 7: Checksum
        byte7 = (byte0 + byte1 + byte2 + byte3 + byte4 + byte5 + byte6) % 256

        return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])
