
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
        node = self.__create_node()
        #sc = self.__attach_spotify()
        sc = None
        await self.__connect_nodes(node, sc)
        await self.load_extension(f"src.cogs.Music.Music")
        await self.load_extension(f"src.cogs.Music.WaveLink")



    async def on_ready(self) -> None:
        await self.tree.sync(guild=Object(id=928785387239915540))
        print("{} si e' connesso a discord!".format(self.user))

    def __create_node(self) -> wavelink.Node:
        if not (host := os.getenv('DOCKER_LAVALINK_HOST')):
            host = '127.0.0.1'
        return wavelink.Node(
            uri=f'http://{host}:2333',
            password='susano',
        )

    def __attach_spotify(self):
        if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
            return spotify.SpotifyClient(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
            )
        return None

    async def __connect_nodes(self, nodes: wavelink.Node, sc) -> None:
        if isinstance(nodes, wavelink.Node):
            nodes = [nodes]
        try:
            await wavelink.Pool.connect(
                nodes=nodes,
                client=self,
            )
        except Exception as e:
            print("Errore nella connessione al nodo: ", e)


if __name__ == "__main__":
    load_dotenv()
    SusanoMusicBot().run(os.getenv("DISCORD_TOKEN"))
