from discord import Object, ext

from src.cogs.Music.event.EventHandler import EventHandler
from src.embed.Embed import Embed

import wavelink
from discord.ext import commands

from src.voice.voice_channel.VoiceChannel import VoiceChannel


class WaveLink(ext.commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__embed = Embed()
        self.__event_handler: EventHandler = bot.event_handler

    @commands.Cog.listener()
    async def on_node_join(self, node, event):
        print(node)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f'Nodo: <{node}> pronto!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        self.__event_handler.set(payload.player.guild.id)


async def setup(bot: ext.commands.Bot):
    await bot.add_cog(WaveLink(bot), guilds=[Object(id=928785387239915540)])
