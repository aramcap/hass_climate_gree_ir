"""Config flow for Gree/Daitsu AC integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default="Gree AC"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]

    try:
        import broadlink
    except ImportError as err:
        raise CannotConnect("Broadlink library not installed") from err

    try:
        # Test connection to Broadlink device
        device = await hass.async_add_executor_job(_test_connection, host)
    except Exception as err:
        _LOGGER.error("Error connecting to Broadlink device at %s: %s", host, err)
        raise CannotConnect(f"Cannot connect to Broadlink device at {host}") from err

    return {"title": data.get(CONF_NAME, f"Gree AC {host}")}


def _test_connection(host: str):
    """Test connection to Broadlink device (runs in executor)."""
    import broadlink

    device = broadlink.rm((host, 80), None, None)
    device.auth()
    return device


class GreeACConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gree AC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
