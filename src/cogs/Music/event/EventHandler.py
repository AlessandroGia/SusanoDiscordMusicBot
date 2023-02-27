import asyncio


class EventHandler:

    def __init__(self) -> None:
        self.__events: dict = {}

    def __get_event_by_guild(self, guild) -> asyncio.Event:
        return self.__events.get(guild)

    def add_event(self, guild) -> None:
        self.__events[guild] = asyncio.Event()

    def is_set(self, guild) -> bool:
        return self.__get_event_by_guild(guild).is_set()

    def clear(self, guild) -> None:
        return self.__get_event_by_guild(guild).clear()

    def set(self, guild) -> None:
        return self.__get_event_by_guild(guild).set()

    async def wait(self, guild):
        return await self.__get_event_by_guild(guild).wait()
