import logging

import voluptuous as vol
from homeassistant import config_entries
from typing import Optional

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TomahConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSON = 1

    def __init__(self):
        pass

    async def async_step_user(self, info: Optional[dict] = None):
        if info is not None:
            _LOGGER.warning(f"config info: {info}")
            return self.async_create_entry(title=DOMAIN, data=info)

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
