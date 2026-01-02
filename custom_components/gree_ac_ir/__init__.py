"""The Gree AC IR integration.

This integration creates climate entities that control Gree air conditioners
by generating IR commands and sending them via existing Broadlink remotes
configured in Home Assistant.
"""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_BROADLINK_ENTITY, CONF_SWING_SUPPORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree AC IR from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    broadlink_entity = entry.data[CONF_BROADLINK_ENTITY]
    name = entry.data.get(CONF_NAME, "Gree AC")
    swing_support = entry.data.get(CONF_SWING_SUPPORT, False)

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
        "swing_support": swing_support,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Send OFF command to all entities after setup
    async def send_initial_off_command() -> None:
        """Send OFF command to initialize AC state."""
        # Small delay to ensure entities are fully set up
        await asyncio.sleep(2)
        
        # Get all climate entities for this integration
        entity_registry = hass.helpers.entity_registry.async_get(hass)
        entities = [
            entity.entity_id
            for entity in entity_registry.entities.values()
            if entity.config_entry_id == entry.entry_id
            and entity.domain == Platform.CLIMATE
        ]
        
        for entity_id in entities:
            _LOGGER.info("Sending initial OFF command to %s", entity_id)
            try:
                await hass.services.async_call(
                    "climate",
                    "turn_off",
                    {"entity_id": entity_id},
                    blocking=True,
                )
            except Exception as err:
                _LOGGER.warning(
                    "Failed to send initial OFF command to %s: %s",
                    entity_id,
                    err,
                )

    # Schedule the initial OFF command
    hass.async_create_task(send_initial_off_command())

    # Reload entry when options are updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
