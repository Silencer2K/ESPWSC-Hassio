import logging

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .core.state import Effect

LOGGER = logging.getLogger(__name__)

DEVICE_NAME = "ESPWSClock {}"
DEVICE_MODEL = "ESPWSClock"

NAME_TRANSLATE = {32: 95, 45: 95, 46: 95}


async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    unique_id = entry.entry_id
    name = entry.title

    light = ClockLight(api, name, unique_id)
    api.add_update_callback(light._update_handler)

    async_add_entities([light])


class ClockLight(LightEntity):
    _attr_has_entity_name = True

    _attr_should_poll = False

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = [e.value for e in Effect]

    def __init__(self, api, name, unique_id):
        self._api = api

        self._attr_name = "Light"
        self._attr_unique_id = "{}-light".format(unique_id)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            default_name=DEVICE_NAME.format(name).translate(NAME_TRANSLATE),
            default_model=DEVICE_MODEL,
        )

        self._update_attributes()

    def _update_attributes(self):
        if self._api.state is not None:
            self._attr_device_info["sw_version"] = self._api.state.info.version

            self._attr_brightness = self._api.state.light.color.brightness
            self._attr_rgb_color = [
                self._api.state.light.color.rgb.red,
                self._api.state.light.color.rgb.green,
                self._api.state.light.color.rgb.blue,
            ]

            self._attr_effect = self._api.state.light.color.effect.value

    def _update_handler(self):
        self._update_attributes()
        self.schedule_update_ha_state()

    @property
    def state(self):
        if self._api.state is None:
            return STATE_UNAVAILABLE
        if self._api.state.light.state:
            return STATE_ON
        return STATE_OFF

    @property
    def is_on(self):
        return self.state == STATE_ON

    async def async_turn_on(self, **kwargs):
        params = {"state": True, "color": {}}
        if "brightness" in kwargs:
            params["color"]["brightness"] = kwargs["brightness"]
        if "rgb_color" in kwargs:
            params["color"]["rgb"] = kwargs["rgb_color"]
        if "effect" in kwargs:
            params["color"]["effect"] = Effect(kwargs["effect"]).name.lower()

        await self._api.async_update("light", params)

    async def async_turn_off(self, **kwargs):
        await self._api.async_update("light", {"state": False})
