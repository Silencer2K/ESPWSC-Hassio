import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST

from .api import API
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


class ESPWSClockConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            api = API(host=user_input[CONF_HOST])

            await api.async_fetch()
            if api.state is not None and api.state.info.name == "ESPWSClock":
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

            errors[CONF_HOST] = "invalid_host"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                }
            ),
            errors=errors,
        )
