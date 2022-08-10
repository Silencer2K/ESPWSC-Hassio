import logging

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .core.state import EFFECT_FX1_AVAILABLE, EFFECT_FX2_AVAILABLE, Effect

LOGGER = logging.getLogger(__name__)

DEVICE_NAME = "ESPWSClock {}"
DEVICE_MODEL = "ESPWSClock"

NAME_TRANSLATE = {32: 95, 45: 95, 46: 95}


async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    unique_id = entry.entry_id
    name = entry.title

    light = Light(api, name, unique_id)
    api.add_update_callback(light._update_handler)

    light_fx1 = LightFx1(api, name, unique_id)
    api.add_update_callback(light_fx1._update_handler)

    light_fx2 = LightFx2(api, name, unique_id)
    api.add_update_callback(light_fx2._update_handler)

    async_add_entities([light, light_fx1, light_fx2])


class _BaseEntity:
    _attr_should_poll = False

    def __init__(self, api, name, unique_id):
        self._api = api

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            default_name=DEVICE_NAME.format(name).translate(NAME_TRANSLATE),
            default_model=DEVICE_MODEL,
        )

        self._update_attributes()

    def _update_attributes(self):
        if self._api.state is not None:
            self._attr_device_info["sw_version"] = self._api.state.info.version

    def _update_handler(self):
        self._update_attributes()
        self.schedule_update_ha_state()

    @property
    def state(self):
        if self._api.state is None:
            return STATE_UNAVAILABLE

        return STATE_OFF

    @property
    def is_on(self):
        return self.state == STATE_ON


class Light(_BaseEntity, LightEntity):
    _attr_has_entity_name = True

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = [e.value for e in Effect]

    def __init__(self, api, name, unique_id):
        super().__init__(api, name, unique_id)

        self._attr_name = "Light"
        self._attr_unique_id = "{}-light".format(unique_id)

    def _update_attributes(self):
        super()._update_attributes()

        if self._api.state is not None:
            self._attr_brightness = self._api.state.light.brightness
            self._attr_rgb_color = [
                self._api.state.light.color.red,
                self._api.state.light.color.green,
                self._api.state.light.color.blue,
            ]

            self._attr_effect = self._api.state.light.effect.value

    @property
    def state(self):
        if self._api.state is None:
            return STATE_UNAVAILABLE

        if self._api.state.light.state:
            return STATE_ON

        return STATE_OFF

    async def async_turn_on(self, **kwargs):
        params = {"state": True}
        if "brightness" in kwargs:
            params["brightness"] = kwargs["brightness"]
        if "rgb_color" in kwargs:
            params["color"] = kwargs["rgb_color"]
        if "effect" in kwargs:
            params["effect"] = Effect(kwargs["effect"]).name.lower()

        await self._api.async_update("light", params)

    async def async_turn_off(self, **kwargs):
        await self._api.async_update("light", {"state": False})


class LightFx1(_BaseEntity, LightEntity):
    _attr_has_entity_name = True

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, api, name, unique_id):
        super().__init__(api, name, unique_id)

        self._attr_name = "Light Fx1"
        self._attr_unique_id = "{}-light-fx1".format(unique_id)

    def _update_attributes(self):
        super()._update_attributes()

        if self._api.state is not None:
            self._attr_brightness = self._api.state.light.brightness
            self._attr_rgb_color = [
                self._api.state.light.effect_color_1.red,
                self._api.state.light.effect_color_1.green,
                self._api.state.light.effect_color_1.blue,
            ]

    @property
    def state(self):
        if (
            self._api.state is None
            or self._api.state.light.effect not in EFFECT_FX1_AVAILABLE
        ):
            return STATE_UNAVAILABLE

        if self._api.state.light.state:
            return STATE_ON

        return STATE_OFF

    async def async_turn_on(self, **kwargs):
        params = {"state": True}
        if "brightness" in kwargs:
            params["brightness"] = kwargs["brightness"]
        if "rgb_color" in kwargs:
            params["effect_color_1"] = kwargs["rgb_color"]

        await self._api.async_update("light", params)

    async def async_turn_off(self, **kwargs):
        await self._api.async_update("light", {"state": False})


class LightFx2(_BaseEntity, LightEntity):
    _attr_has_entity_name = True

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, api, name, unique_id):
        super().__init__(api, name, unique_id)

        self._attr_name = "Light Fx2"
        self._attr_unique_id = "{}-light-fx2".format(unique_id)

    def _update_attributes(self):
        super()._update_attributes()

        if self._api.state is not None:
            self._attr_brightness = self._api.state.light.brightness
            self._attr_rgb_color = [
                self._api.state.light.effect_color_2.red,
                self._api.state.light.effect_color_2.green,
                self._api.state.light.effect_color_2.blue,
            ]

    @property
    def state(self):
        if (
            self._api.state is None
            or self._api.state.light.effect not in EFFECT_FX2_AVAILABLE
        ):
            return STATE_UNAVAILABLE

        if self._api.state.light.state:
            return STATE_ON

        return STATE_OFF

    async def async_turn_on(self, **kwargs):
        params = {"state": True}
        if "brightness" in kwargs:
            params["brightness"] = kwargs["brightness"]
        if "rgb_color" in kwargs:
            params["effect_color_2"] = kwargs["rgb_color"]

        await self._api.async_update("light", params)

    async def async_turn_off(self, **kwargs):
        await self._api.async_update("light", {"state": False})
