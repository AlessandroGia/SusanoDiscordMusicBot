from src.voice.voice_state.timeouts.Timeout import Timeout

import asyncio


class TimeoutPause(Timeout):
    def __init__(self, ist) -> None:

        self.__timeout: int = (180)
        self.__event: asyncio.Event = asyncio.Event()
        self.__ist = ist

        self.__timeout_coro: asyncio.Task = None

    def set(self) -> None:
        self.__event.set()

    def clear(self) -> None:
        self.__event.clear()

    def cancel(self) -> None:
        if self.__timeout_coro and not self.__timeout_coro.done():
            self.__timeout_coro.cancel()

    async def run(self) -> None:
        self.__timeout_coro = self.__ist.bot.loop.create_task(self.__coro())

    async def __coro(self) -> None:
        try:
            print("Aspettando l'unpause")
            await self._wait(self.__event, self.__timeout)
            print("Unpausato")
        except asyncio.TimeoutError:
            print("Timeout: troppo tempo in pausa")
            await self.__ist.leave()
