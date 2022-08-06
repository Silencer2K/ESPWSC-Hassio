import logging
from enum import Enum

import attr

LOGGER = logging.getLogger(__name__)


class JsonError(Exception):
    pass


@attr.s()
class RGB:
    red = attr.ib(default=0)
    green = attr.ib(default=0)
    blue = attr.ib(default=0)

    def from_json(self, data):
        assert isinstance(data, list)

        assert len(data) == 3

        assert isinstance(data[0], int)
        assert isinstance(data[1], int)
        assert isinstance(data[2], int)

        self.red, self.green, self.blue = data


class Effect(Enum):
    NONE = "None"


@attr.s()
class Light:
    state = attr.ib(default=False)
    brightness = attr.ib(default=0)
    color = attr.ib(default=RGB())
    effect = attr.ib(default=Effect.NONE)

    def from_json(self, data):
        assert isinstance(data, dict)

        if "state" in data:
            assert isinstance(data["state"], bool)
            self.state = data["state"]
        if "brightness" in data:
            assert isinstance(data["brightness"], int)
            self.brightness = data["brightness"]
        if "color" in data:
            self.color.from_json(data["color"])
        if "effect" in data:
            self.effect = Effect[data["effect"].upper()]


@attr.s()
class WiFi:
    ssid = attr.ib(default="")
    password = attr.ib(default="")

    def from_json(self, data):
        assert isinstance(data, dict)

        if "ssid" in data:
            assert isinstance(data["ssid"], str)
            self.ssid = data["ssid"]
        if "password" in data:
            assert isinstance(data["password"], str)
            self.password = data["password"]


@attr.s()
class System:
    tz = attr.ib(default="")
    sntp = attr.ib(default="")

    def from_json(self, data):
        assert isinstance(data, dict)

        if "tz" in data:
            assert isinstance(data["tz"], str)
            self.tz = data["tz"]
        if "sntp" in data:
            assert isinstance(data["sntp"], str)
            self.sntp = data["sntp"]


@attr.s()
class Info:
    name = attr.ib(default="")
    version = attr.ib(default="")

    def from_json(self, data):
        assert isinstance(data, dict)

        if "name" in data:
            assert isinstance(data["name"], str)
            self.name = data["name"]
        if "version" in data:
            assert isinstance(data["version"], str)
            self.version = data["version"]


@attr.s()
class State:
    light = attr.ib(default=Light())
    wifi = attr.ib(default=WiFi())
    system = attr.ib(default=System())
    info = attr.ib(default=Info())

    def from_json(self, data):
        assert isinstance(data, dict)

        if "light" in data:
            self.light.from_json(data["light"])
        if "wifi" in data:
            self.wifi.from_json(data["wifi"])
        if "system" in data:
            self.system.from_json(data["system"])
        if "info" in data:
            self.info.from_json(data["info"])
