
from discord import Intents, Object, Status, Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv

import os
import asyncio
import wavelink
import logging

from src.cogs.Music.event.EventHandler import EventHandler
from src.voice.voice_channel.VoiceChannel import VoiceChannel


class SusanoMusicBot(commands.Bot):
    def __init__(self) -> None:
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=Intents.all(),
            status=Status.do_not_disturb,
            activity=Activity(type=ActivityType.listening, name="Broken Music")
        )
        self.vc: VoiceChannel = VoiceChannel(self)
        self.event_handler: EventHandler = EventHandler()

    async def setup_hook(self) -> None:
        await self.load_extension(f"src.cogs.Music.Music")
        await self.load_extension(f"src.cogs.Music.WaveLink")

    async def on_ready(self) -> None:
        await self.tree.sync(guild=Object(id=928785387239915540))
        await self.__create_node(10)
        print("{} si e' connesso a discord!".format(self.user))

    async def __create_node(self, i):
        if not (host := os.getenv('DOCKER_LAVALINK_HOST')):
             host = '127.0.0.1'
        logging.info(host)
        for x in range(i):
            self.node: wavelink.Node = await wavelink.NodePool.create_node(
                bot=self,
                host=host,
                port=2333,
                password='susano'
            )
            if self.node.is_connected():
                break
            await asyncio.sleep(1)
        logging.info(self.node)


if __name__ == "__main__":
    load_dotenv()
    SusanoMusicBot().run(os.getenv("DISCORD_TOKEN"))
