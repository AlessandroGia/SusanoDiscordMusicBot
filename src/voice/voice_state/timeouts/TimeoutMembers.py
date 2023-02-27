from src.voice.voice_state.timeouts.Timeout import Timeout

import asyncio


class TimeoutMembers(Timeout):

    def __init__(self, ist) -> None:
        self.__timeout: int = (120)
        self.__event: asyncio.Event = asyncio.Event()

        self.__ist = ist
        self.__timeout_coro: asyncio.Task = None
        self.__timeout_coro1: asyncio.Task = None

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
        await asyncio.sleep(1)
        while True:
            try:
                if not self.__ist.voice.channel.voice_states.get(self.__ist.bot.application_id):
                    await self.__ist.leave()
                await asyncio.sleep(0.5)
                if self.__num_members_in_vc() == 0:
                    self.clear()
                    if not self.__timeout_coro1:
                        self.__timeout_coro1 = self.__ist.bot.loop.create_task(self.__timeout_no_members_coro())
                else:
                    self.set()
                    if self.__timeout_coro1:
                        self.__timeout_coro1.cancel()
                        self.__timeout_coro1 = None
            except Exception as e:
                print('TimeoutMember, errore:', e)

    async def __timeout_no_members_coro(self) -> None:
        try:
            print('Aspettando almeno una persona in vc')
            await self._wait(self.__event, self.__timeout)
            print('Una persona e\' entrata')
        except asyncio.TimeoutError:
            print('Timeout: nessuna persona in vc')
            await self.__ist.leave()

    def __num_members_in_vc(self) -> int:
        return len([x for x in self.__ist.voice.channel.members if not x.bot])

