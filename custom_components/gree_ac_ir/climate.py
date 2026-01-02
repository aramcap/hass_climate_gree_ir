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
                "Sending Gree IR to %s - Mode: %s, Temp: %d, Fan: %s, "
                "Gree bytes: [%s], IR packet length: %d, Base64 payload: b64:%s",
                self._broadlink_entity,
                self._hvac_mode,
                self._target_temperature,
                self._fan_mode,
                " ".join(f"{b:02X}" for b in gree_bytes),
                len(ir_packet),
                b64_command,
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
        """Build Gree protocol 4-byte command.

        Based on actual IR codes analysis from working Daitsu/Gree remote:
        Byte 0: Mode (3 bits) + Power (1 bit) + Fan (2 bits)
        Byte 1: Temperature (value = temp - 16, range 0-14)
        Byte 2: 0x60 when ON, 0x20 when OFF
        Byte 3: 0x50 constant
        """
        power = 1 if self._hvac_mode != HVACMode.OFF else 0
        
        # Get mode bits (use current mode, or keep last mode when off)
        if self._hvac_mode == HVACMode.OFF:
            mode_bits = GREE_MODES.get("cool", 0x01)
        else:
            mode_bits = GREE_MODES.get(self._hvac_mode.value, 0x01)
        
        fan_bits = GREE_FAN_MODES.get(self._fan_mode, 0b00)
        
        byte0 = (mode_bits & 0x07) | (power << 3) | ((fan_bits & 0x03) << 4)
        byte1 = max(0, min(14, self._target_temperature - 16))
        byte2 = 0x60 if power else 0x20
        byte3 = 0x50

        return bytes([byte0, byte1, byte2, byte3])

    def _encode_ir_packet(self, gree_bytes: bytes) -> bytes:
        """Encode Gree 4 bytes to Broadlink IR packet format.

        Structure (identical to original Daitsu/Gree remote):
        - Frame 1: Header + 32 bits (4 bytes) + 3-bit connector (010) + footer
        - Frame break: 0x00 0x02 + gap timing
        - Frame 2: 28 zero bits + 4-bit checksum + footer
        """
        # Timing values in Broadlink raw units (NOT microseconds)
        # These produce signals identical to the original remote
        HDR_MARK = 0x011F  # 287 -> ~8740µs
        HDR_SPACE = 0x90   # 144 -> ~4385µs
        BIT_MARK = 20      # -> ~609µs
        ZERO_SPACE = 18    # -> ~548µs
        ONE_SPACE = 54     # -> ~1644µs
        FOOTER = 19        # -> ~578µs
        GAP = 0x81         # 129 -> ~3928µs
        
        # Build Frame 1
        frame1 = bytearray()
        
        # Header (extended format for values > 255)
        frame1.extend([0x00, (HDR_MARK >> 8) & 0xFF, HDR_MARK & 0xFF])
        frame1.append(HDR_SPACE)
        
        # 4 bytes = 32 bits, LSB first
        for byte in gree_bytes[:4]:
            for i in range(8):
                bit = (byte >> i) & 1
                frame1.append(BIT_MARK)
                frame1.append(ONE_SPACE if bit else ZERO_SPACE)
        
        # Connector: 3 bits (010 LSB first)
        frame1.extend([BIT_MARK, ZERO_SPACE])  # bit 0
        frame1.extend([BIT_MARK, ONE_SPACE])   # bit 1
        frame1.extend([BIT_MARK, ZERO_SPACE])  # bit 0
        
        # Footer mark
        frame1.append(FOOTER)
        
        # Frame break + gap
        frame_break = bytearray([0x00, 0x02, GAP])
        
        # Calculate Frame 2 checksum: ((b0 & 0xF) + (b1 & 0xF) + 0xA) & 0xF
        checksum = ((gree_bytes[0] & 0x0F) + (gree_bytes[1] & 0x0F) + 0x0A) & 0x0F
        
        # Frame 2: 28 zero bits + 4-bit checksum + footer
        frame2 = bytearray()
        
        # 28 zero bits (56 bytes: mark-space pairs)
        for _ in range(28):
            frame2.append(BIT_MARK)
            frame2.append(ZERO_SPACE)
        
        # 4-bit checksum (LSB first)
        for i in range(4):
            bit = (checksum >> i) & 1
            frame2.append(BIT_MARK)
            frame2.append(ONE_SPACE if bit else ZERO_SPACE)
        
        # Footer (mark + terminator)
        frame2.append(BIT_MARK)
        frame2.append(0x00)
        
        # Combine all parts
        ir_data = frame1 + frame_break + frame2
        
        # Build Broadlink packet
        packet = bytearray()
        packet.append(0x26)  # IR type
        packet.append(0x00)  # No repeat
        
        # Length includes end markers (0x0D 0x05)
        total_len = len(ir_data) + 2
        packet.append(total_len & 0xFF)
        packet.append((total_len >> 8) & 0xFF)
        
        packet.extend(ir_data)
        packet.append(0x0D)  # End marker
        packet.append(0x05)  # End marker
        
        return bytes(packet)
