import asyncio
import json
import logging

import attr
import httpx

LOGGER = logging.getLogger(__name__)

TIMEOUT = 5.0

EVENTS_READ_TIMEOUT = 30.0
EVENTS_RECONNECT = 30.0

API_URL = "http://{}/api/{}"
EVENTS_URL = "http://{}/api/events"


async def events(resp):
    event = {}
    async for line in resp.aiter_lines():
        if line[-1] == "\n":
            line = line[:-1]
        if line == "" and len(event) != 0:
            if "data" not in event:
                raise EventError("Invalid event data")
            yield Event(**event)
            event = {}
            continue
        part = line.split(": ", 2)
        if len(part) != 2 or part[0] not in ["id", "event", "data"]:
            raise EventError("Invalid event data")
        if part[0] == "data":
            if part[0] in event:
                event[part[0]] += "\n" + part[1]
            else:
                event[part[0]] = part[1]
        else:
            if part[0] in event:
                raise EventError("Invalid event data")
            event[part[0]] = part[1]


class EventError(Exception):
    pass


@attr.s()
class Event:
    id = attr.ib()
    event = attr.ib()
    data = attr.ib()


class Request:
    def __init__(self, host=None, callback=None):
        self._host = host
        self._callback = callback

        self._events_task = None

    async def async_task(self):
        loop = asyncio.get_running_loop()

        LOGGER.info("Starting background tasks")
        self._events_task = loop.create_task(self._async_events_task())

        try:
            while True:
                await asyncio.sleep(1)

                if self._events_task.done():
                    LOGGER.info("Restarting events task")
                    self._events_task = loop.create_task(self._async_events_task())

        except asyncio.CancelledError:
            LOGGER.info("Canceling background tasks")
            self._events_task.cancel()

    async def _async_events_task(self):
        LOGGER.info("Events task started")

        while True:
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        method="GET",
                        url=EVENTS_URL.format(self._host),
                        timeout=httpx.Timeout(TIMEOUT, read=EVENTS_READ_TIMEOUT),
                    ) as resp:
                        resp.raise_for_status()

                        try:
                            async for event in events(resp):
                                self._callback(event.event, json.loads(event.data))

                        except httpx.ReadTimeout:
                            continue

            except asyncio.CancelledError:
                LOGGER.info("Events task canceled")
                raise

            except (
                httpx.HTTPStatusError,
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                json.JSONDecodeError,
                EventError,
            ) as e:
                LOGGER.error("%s exception occurred", type(e).__name__)
                LOGGER.info("%s exception occurred", type(e).__name__, exc_info=True)

                self._callback("error")

            LOGGER.info("Sleeping for %d seconds", EVENTS_RECONNECT)
            await asyncio.sleep(EVENTS_RECONNECT)

        LOGGER.info("Events task finished")

    async def _async_request(self, method=None, post=None):
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method="GET" if post is None else "POST",
                url=API_URL.format(self._host, method),
                json=post,
                timeout=httpx.Timeout(TIMEOUT),
            )
            resp.raise_for_status()

            return resp.json()

    async def async_request(self, method="status", post=None):
        try:
            data = await self._async_request(method=method, post=post)

        except (
            httpx.HTTPStatusError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            json.JSONDecodeError,
        ) as e:
            LOGGER.error("%s exception occurred", type(e).__name__)
            LOGGER.info("%s exception occurred", type(e).__name__, exc_info=True)

            if self._events_task is not None:
                self._events_task.cancel()

            self._callback("error")
        else:
            self._callback(method, data)
