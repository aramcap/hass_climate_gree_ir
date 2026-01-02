"""The Gree/Daitsu Air Conditioner IR integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree AC from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]

    try:
        import broadlink

        device = await hass.async_add_executor_job(
            _setup_broadlink_device, host
        )
    except ImportError:
        _LOGGER.error("Broadlink library not installed")
        raise ConfigEntryNotReady("Broadlink library not installed")
    except Exception as err:
        _LOGGER.error("Error connecting to Broadlink device at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Error connecting to Broadlink device: {err}")

    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "host": host,
        "name": entry.data.get(CONF_NAME, f"Gree AC {host}"),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _setup_broadlink_device(host: str):
    """Set up the Broadlink device (runs in executor)."""
    import broadlink

    device = broadlink.rm((host, 80), None, None)
    device.auth()
    return device


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
