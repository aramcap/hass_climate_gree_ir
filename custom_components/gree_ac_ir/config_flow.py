"""Config flow for Gree AC IR integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import CONF_BROADLINK_ENTITY, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _get_broadlink_remotes(hass: HomeAssistant) -> list[str]:
    """Get list of Broadlink remote entities."""
    entity_reg = er.async_get(hass)
    remotes = []
    
    for entity in entity_reg.entities.values():
        if entity.domain == "remote" and entity.platform == "broadlink":
            remotes.append(entity.entity_id)
    
    return remotes


class GreeACIRConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gree AC IR."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return GreeACIROptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Get available Broadlink remotes
        broadlink_remotes = _get_broadlink_remotes(self.hass)

        if user_input is not None:
            broadlink_entity = user_input[CONF_BROADLINK_ENTITY]
            
            # Check if already configured with this Broadlink entity
            await self.async_set_unique_id(broadlink_entity)
            self._abort_if_unique_id_configured()

            # Verify the entity exists
            state = self.hass.states.get(broadlink_entity)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                title = user_input.get(CONF_NAME, f"Gree AC ({broadlink_entity})")
                return self.async_create_entry(title=title, data=user_input)

        # Build schema dynamically with available remotes
        if broadlink_remotes:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_BROADLINK_ENTITY): EntitySelector(
                        EntitySelectorConfig(
                            domain="remote",
                            integration="broadlink",
                        )
                    ),
                    vol.Optional(CONF_NAME, default="Gree AC"): TextSelector(),
                }
            )
        else:
            # No Broadlink remotes found, allow manual entry
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_BROADLINK_ENTITY): TextSelector(),
                    vol.Optional(CONF_NAME, default="Gree AC"): TextSelector(),
                }
            )
            errors["base"] = "no_broadlink_found"

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class GreeACIROptionsFlow(OptionsFlow):
    """Handle options flow for Gree AC IR."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            broadlink_entity = user_input[CONF_BROADLINK_ENTITY]
            
            # Verify the entity exists
            state = self.hass.states.get(broadlink_entity)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                # Update the config entry data
                new_data = {**self.config_entry.data, **user_input}
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                    title=user_input.get(CONF_NAME, self.config_entry.title),
                )
                return self.async_create_entry(title="", data={})

        # Get current values
        current_broadlink = self.config_entry.data.get(CONF_BROADLINK_ENTITY, "")
        current_name = self.config_entry.data.get(CONF_NAME, "Gree AC")

        # Get available Broadlink remotes
        broadlink_remotes = _get_broadlink_remotes(self.hass)

        if broadlink_remotes:
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BROADLINK_ENTITY, default=current_broadlink
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain="remote",
                            integration="broadlink",
                        )
                    ),
                    vol.Optional(CONF_NAME, default=current_name): TextSelector(),
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BROADLINK_ENTITY, default=current_broadlink
                    ): TextSelector(),
                    vol.Optional(CONF_NAME, default=current_name): TextSelector(),
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
