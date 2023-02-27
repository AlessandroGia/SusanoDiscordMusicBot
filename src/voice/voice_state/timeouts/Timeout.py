from abc import ABC, abstractmethod
import asyncio


class Timeout(ABC):

    @abstractmethod
    async def run(self, *args):
        pass

    async def _wait(self, event: asyncio.Event, timeout: int):
        await asyncio.wait_for(event.wait(), timeout=timeout)

