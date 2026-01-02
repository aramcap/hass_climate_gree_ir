"""Climate platform for Gree AC IR integration.

This integration creates a climate entity that builds Gree IR commands
and sends them via an existing Broadlink integration in Home Assistant.
"""
from __future__ import annotations

import base64
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
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BROADLINK_ENTITY,
    CONF_SWING_SUPPORT,
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
        name=data["name"],
        broadlink_entity=data["broadlink_entity"],
        unique_id=config_entry.entry_id,
        swing_support=data.get("swing_support", False),
    )
    async_add_entities([entity])


class GreeACClimate(ClimateEntity):
    """Climate entity for Gree AC controlled via Broadlink."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP
    _attr_hvac_modes = HVAC_MODES
    _attr_fan_modes = FAN_MODES

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        broadlink_entity: str,
        unique_id: str,
        swing_support: bool = False,
    ) -> None:
        """Initialize the Gree AC climate entity."""
        self.hass = hass
        self._broadlink_entity = broadlink_entity
        self._swing_support = swing_support

        # Set supported features based on swing support
        features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        if swing_support:
            features |= ClimateEntityFeature.SWING_MODE
            self._attr_swing_modes = SWING_MODES
        
        self._attr_supported_features = features

        # Entity attributes
        self._attr_unique_id = f"gree_ac_ir_{unique_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=name,
            manufacturer=MANUFACTURER,
            model="Gree Air Conditioner",
        )

        # AC state
        self._hvac_mode = HVACMode.OFF
        self._target_temperature = 24
        self._current_temperature: float | None = None
        self._fan_mode = "auto"
        self._swing_mode = "off"

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
        if not self._swing_support:
            return
        if hasattr(self, "_attr_swing_modes") and swing_mode in self._attr_swing_modes:
            self._swing_mode = swing_mode
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
        """Build IR payload and send via Broadlink integration."""
        try:
            # Build Gree IR payload
            gree_bytes = self._build_gree_command()
            ir_packet = self._encode_ir_packet(gree_bytes)

            # Convert to base64 (format used by Broadlink integration)
            b64_command = base64.b64encode(ir_packet).decode("utf-8")

            _LOGGER.debug(
                "Sending Gree IR to %s - Mode: %s, Temp: %d, Fan: %s, Bytes: %s",
                self._broadlink_entity,
                self._hvac_mode,
                self._target_temperature,
                self._fan_mode,
                " ".join(f"{b:02X}" for b in gree_bytes),
            )

            # Send via Broadlink remote.send_command service
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": self._broadlink_entity,
                    "command": f"b64:{b64_command}",
                },
                blocking=True,
            )

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Error sending IR command: %s", err)

    def _build_gree_command(self) -> bytes:
        """Build Gree protocol 8-byte command.

        Based on actual IR codes analysis:
        - Part 1 (bytes 0-3): Main command
        - Part 2 (bytes 4-7): Extended data (mostly zeros) + checksum

        Byte 0: Mode (3 bits) + Power (1 bit) + Fan (2 bits) + extras
        Byte 1: Temperature (4 bits, value = temp - 16)
        Byte 2: 0x60 when ON, 0x20 when OFF (Light/features)
        Byte 3: 0x50 constant
        Bytes 4-6: 0x00
        Byte 7: Checksum = (((byte0 & 0x0F) + (byte1 & 0x0F) + 10) & 0x0F) << 4
        """
        # Byte 0: Mode (3 bits) + Power (1 bit) + Fan (2 bits)
        power = 1 if self._hvac_mode != HVACMode.OFF else 0
        
        # Get mode bits (use current mode, or keep last mode when off)
        if self._hvac_mode == HVACMode.OFF:
            # When turning off, we still need a valid mode
            mode_bits = GREE_MODES.get("cool", 0x01)
        else:
            mode_bits = GREE_MODES.get(self._hvac_mode.value, 0x01)
        
        fan_bits = GREE_FAN_MODES.get(self._fan_mode, 0b00)
        
        byte0 = (mode_bits & 0x07) | (power << 3) | ((fan_bits & 0x03) << 4)

        # Byte 1: Temperature (offset from 16°C)
        temp_bits = max(0, min(14, self._target_temperature - 16))
        byte1 = temp_bits & 0x0F

        # Byte 2: 0x60 = ON features (light on, etc), 0x20 = OFF
        byte2 = 0x60 if power else 0x20

        # Byte 3: Constant
        byte3 = 0x50

        # Bytes 4-6: Reserved (zeros)
        byte4 = 0x00
        byte5 = 0x00
        byte6 = 0x00

        # Byte 7: Checksum
        # Formula: (((byte0 & 0x0F) + (byte1 & 0x0F) + 10) & 0x0F) << 4
        checksum = (((byte0 & 0x0F) + (byte1 & 0x0F) + 10) & 0x0F) << 4
        byte7 = checksum

        return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])

    def _encode_ir_packet(self, gree_bytes: bytes) -> bytes:
        """Encode Gree bytes to Broadlink IR packet format.

        Gree YAC1FB IR timing:
        - Header: 9000µs mark + 4500µs space
        - Bit 0: 620µs mark + 540µs space
        - Bit 1: 620µs mark + 1680µs space
        - Connector: 3-bit (010) + 620µs mark + 20000µs space
        - Footer: 620µs mark
        """
        # Timing constants (microseconds)
        HDR_MARK = 9000
        HDR_SPACE = 4500
        BIT_MARK = 620
        ONE_SPACE = 1680
        ZERO_SPACE = 540
        MSG_SPACE = 20000

        # Broadlink time unit ≈ 32.84µs (269/8192 seconds)
        BL_UNIT = 32.84

        def to_bl(us: int) -> int:
            return int(us / BL_UNIT)

        timings: list[int] = []

        def add_mark_space(mark: int, space: int) -> None:
            timings.append(to_bl(mark))
            timings.append(to_bl(space))

        def add_byte(b: int) -> None:
            """Send byte LSB first."""
            for _ in range(8):
                if b & 1:
                    add_mark_space(BIT_MARK, ONE_SPACE)
                else:
                    add_mark_space(BIT_MARK, ZERO_SPACE)
                b >>= 1

        # Header
        add_mark_space(HDR_MARK, HDR_SPACE)

        # First 4 bytes
        for i in range(4):
            add_byte(gree_bytes[i])

        # 3-bit connector (010 LSB first = 0, 1, 0)
        add_mark_space(BIT_MARK, ZERO_SPACE)
        add_mark_space(BIT_MARK, ONE_SPACE)
        add_mark_space(BIT_MARK, ZERO_SPACE)

        # Message gap
        add_mark_space(BIT_MARK, MSG_SPACE)

        # Second header
        add_mark_space(HDR_MARK, HDR_SPACE)

        # Last 4 bytes
        for i in range(4, 8):
            add_byte(gree_bytes[i])

        # Footer mark
        timings.append(to_bl(BIT_MARK))

        return self._build_broadlink_packet(timings)

    def _build_broadlink_packet(self, timings: list[int]) -> bytes:
        """Convert timings to Broadlink packet format.

        Format:
        - 0x26: IR type
        - 0x00: No repeat
        - 2 bytes: data length (little endian)
        - timing data (values > 255 use 3-byte extended format: 0x00, high, low)
        - 0x0D, 0x05: end markers
        - padding to 16-byte boundary
        """
        data = bytearray()

        for t in timings:
            if t > 255:
                data.append(0x00)
                data.append((t >> 8) & 0xFF)
                data.append(t & 0xFF)
            else:
                data.append(t)

        packet = bytearray()
        packet.append(0x26)
        packet.append(0x00)
        packet.append(len(data) & 0xFF)
        packet.append((len(data) >> 8) & 0xFF)
        packet.extend(data)
        packet.append(0x0D)
        packet.append(0x05)

        # Pad to 16 bytes
        while len(packet) % 16:
            packet.append(0x00)

        return bytes(packet)
