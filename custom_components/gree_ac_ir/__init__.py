"""The Gree AC IR integration.

This integration creates climate entities that control Gree air conditioners
by generating IR commands and sending them via existing Broadlink remotes
configured in Home Assistant.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_BROADLINK_ENTITY, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree AC IR from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    broadlink_entity = entry.data[CONF_BROADLINK_ENTITY]
    name = entry.data.get(CONF_NAME, "Gree AC")

    # Verify the Broadlink entity exists
    state = hass.states.get(broadlink_entity)
    if state is None:
        _LOGGER.warning(
            "Broadlink entity %s not found. It may not be loaded yet.",
            broadlink_entity,
        )

    hass.data[DOMAIN][entry.entry_id] = {
        "broadlink_entity": broadlink_entity,
        "name": name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
