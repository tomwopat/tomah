import logging
from typing import Optional

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TomahConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSON = 1

    def __init__(self):
        pass

    async def async_step_user(self, user_input: Optional[dict] = None):
        if user_input is not None:
            _LOGGER.warning(f"config info: {user_input}")
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("client_id"): str,
                    vol.Required("domain"): str,
                }
            ),
        )

    async def async_step_reconfigure(self, user_input):
        if user_input is not None:
            _LOGGER.warning(f"config info: {user_input}")
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("client_id"): str,
                    vol.Required("domain"): str,
                }
            ),
        )
