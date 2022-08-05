import logging

from .core.request import Request
from .core.state import State

LOGGER = logging.getLogger(__name__)


class API:
    def __init__(self, host=None):
        self.state = None

        self._request = Request(host=host, callback=self._update_handler)
        self._callbacks = []

    async def async_task(self):
        await self._request.async_task()

    async def async_fetch(self):
        await self._request.async_request()

    async def async_update(self, method=None, post=None):
        await self._request.async_request(method=method, post=post)

    def _update_handler(self, event, data=None):
        if event == "error":
            self.state = None
            for cb in self._callbacks:
                cb()

        elif event != "pong":
            if self.state is None:
                self.state = State()

            try:
                self.state.from_json(data)
            except (AssertionError, ValueError) as e:
                self.state = None
                LOGGER.error("%s exception occurred", type(e).__name__)
                LOGGER.info("%s exception occurred", type(e).__name__, exc_info=True)

            for cb in self._callbacks:
                cb()

    def add_update_callback(self, cb):
        self._callbacks.append(cb)
