from typing import Callable

from discord import Interaction, ext, TextChannel, Message

import asyncio
import wavelink

import logging

import sys

from discord.ext import commands

from discord import Embed

from src.cogs.Music.event.EventHandler import EventHandler
from src.embed.Embed import Song
from src.exceptions.QueueException import *
from src.exceptions.TrackPlayerExceptions import *
from src.voice.voice_state.timeouts.TimeoutMembers import TimeoutMembers
from src.voice.voice_state.timeouts.TimeoutPause import TimeoutPause

from threading import Lock


class VoiceState(ext.commands.Cog):

    TIMEOUT_WAIT_FOR_A_SONG = (600)

    def __init__(self, bot: ext.commands.Bot, del_instance: Callable) -> None:

        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
        self.bot: ext.commands.Bot = bot
        self.__del_instance: Callable = del_instance
        self.__embed: Song = Song()
        self.__lock_queue: Lock = Lock()

        self.voice: wavelink.Player | None = None

        self.__event_handler: EventHandler = self.bot.event_handler

        self.__audio_player: asyncio.Task = None

        self.__timeout_in_pause: TimeoutPause = TimeoutPause(self)
        self.__timeout_members: TimeoutMembers = TimeoutMembers(self)

        self.__queue_tracks: wavelink.Queue | None = None

        self.__current_track: wavelink.Search | None = None
        self.__current_interaction: Interaction | None = None

        self.__loop: bool = False
        self.__loop_all: bool = False

        self.__interaction_flag: bool = False

        self.__channel: TextChannel | None  = None
        self.__channel_embed: Message | None  = None

    def __reset(self):
        self.voice: wavelink.Player = None
        self.__event_handler: EventHandler = self.bot.event_handler
        self.__audio_player: asyncio.Task = None
        self.__timeout_in_pause: TimeoutPause = TimeoutPause(self)
        self.__timeout_members: TimeoutMembers = TimeoutMembers(self)
        self.__queue_tracks: wavelink.Queue | None = None
        self.__current_track: wavelink.Search = None
        self.__current_interaction: Interaction = None
        self.__loop: bool = False
        self.__loop_all: bool = False
        self.__interaction_flag: bool = False
        self.__channel: TextChannel = None
        self.__channel_embed: Message = None

    async def join(self, interaction: Interaction) -> None:
        self.voice: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player
        )
        self.__queue_tracks = self.voice.queue
        self.__channel = interaction.channel
        self.__event_handler.add_event(self.__channel.guild.id)
        self.__audio_player = self.bot.loop.create_task(self.__audio_player_coro())
        await self.__timeout_members.run()

    async def play(self, interaction: Interaction, track: wavelink.Search) -> None:
        if self.__current_track:
            await interaction.response.send_message(
                embed=self.__embed.inCoda(track, interaction.user)
            )
        else:
            self.__interaction_flag = True
            self.__current_interaction = interaction
        await self.__add_to_queue(track)

    async def __add_to_queue(self, track: wavelink.Search) -> None:
        self.__queue_tracks.put(track)

    async def leave(self) -> None:
        if self.voice.playing or self.voice.paused:
            await self.voice.stop()
        await self.voice.disconnect()
        await self.__exit()

    async def remove(self, index: int) -> str:
        if self.__queue_empty():
            raise NoTracksInQueueError
        if index < len(self.__queue_tracks):
            item = self.__queue_tracks[index]
            self.__queue_tracks.delete(index)
            return item.title
        else:
            raise OutOfIndexQueue

    async def shuffle(self) -> None:
        if self.__queue_empty():
            raise NoTracksInQueueError
        self.__queue_tracks.shuffle()

    async def toggle_loop(self) -> bool:
        if not self.__current_track:
            raise NoCurrentTrackError
        if self.__loop_all:
            raise AlreadyLoopAll
        self.__loop = not self.__loop
        await self.__update_current_song()
        return self.__loop

    async def toggle_loop_all(self) -> bool:
        if not self.__current_track:
            raise NoCurrentTrackError
        if self.__loop:
            raise AlreadyLoop
        self.__loop_all = not self.__loop_all
        await self.__update_current_song()
        return self.__loop_all

    async def list_queue(self) -> []:
        if self.__queue_empty():
            raise NoTracksInQueueError
        return self.__queue_tracks

    def __queue_empty(self) -> bool:
        return False if self.__queue_tracks else True

    async def __exit(self) -> None:
        if self.__audio_player:
            self.__audio_player.cancel()
        if self.__timeout_members:
            self.__timeout_members.cancel()
        if self.__timeout_in_pause:
            self.__timeout_in_pause.cancel()
        self.__del_instance(self.__channel.guild.id)
        self.__reset()

    async def toggle_pause(self) -> bool:
        if not self.__current_track:
            raise NoCurrentTrackError
        if self.voice.paused:
            self.__timeout_in_pause.set()
            await self.voice.pause(False)
            self.__timeout_in_pause.cancel()
        elif not self.voice.paused and self.voice.playing:
            await self.voice.pause(True)
            self.__timeout_in_pause.clear()
            await self.__timeout_in_pause.run()
        await self.__update_current_song()
        return self.voice.paused

    async def reset(self):
        self.__queue_tracks.clear()
        if self.__loop:
            self.__loop = False
        if self.__loop_all:
            self.__loop_all = False
        if self.voice.playing or self.voice.paused:
            await self.voice.stop()
            if self.voice.paused:
                await self.toggle_pause()

    async def skip(self) -> None:
        if not self.__current_track:
            raise NoCurrentTrackError
        await self.voice.stop()

    async def __audio_player_coro(self) -> None:
        while True:
            if self.__current_interaction:
                self.__event_handler.clear(self.__channel.guild.id)

            if not self.__loop:
                self.__current_track = None
                try:
                    print(' - Aspettando la canzone dalla coda')
                    with self.__lock_queue:
                        self.__current_track = await asyncio.wait_for(self.__queue_tracks.get_wait(), timeout=self.TIMEOUT_WAIT_FOR_A_SONG)
                    print('Canzone presa dalla coda')
                except asyncio.TimeoutError:
                    await self.leave()
                    return None
            try:
                await self.__send_current_song()
                await self.voice.play(self.__current_track)
                if self.voice.paused:
                    await self.voice.pause(True)
                print(' - Aspettando la fine della canzone')
                await self.__event_handler.wait(self.__channel.guild.id)

                if self.__loop_all and not self.__loop:
                    self.__queue_tracks.put(self.__current_track)

                self.__interaction_flag = False
                print('Canzone Finita')
            except Exception as e:
                print('Errore 2:', e)
                await self.__clean_up_stuck()

    def __embed_in_riproduzione(self) -> Embed:
        return self.__embed.inRiproduzione(
            self.__current_track,
            self.__current_interaction.user,
            in_loop=self.__loop,
            in_loop_all=self.__loop_all,
            in_pause=self.voice.paused
        )

    async def __send_current_song(self):
        if self.__interaction_flag:
            await self.__current_interaction.response.send_message(
                embed=self.__embed_in_riproduzione()
            )
        else:
            self.__channel_embed = await self.__channel.send(
                embed=self.__embed_in_riproduzione()
            )

    async def __update_current_song(self) -> None:
        if self.__interaction_flag:
            await self.__current_interaction.edit_original_response(
                embed=self.__embed_in_riproduzione()
            )
        else:
            await self.__channel_embed.edit(
                embed=self.__embed_in_riproduzione()
            )

    async def __clean_up_stuck(self):
        if self.voice.playing or self.voice.paused:
            await self.voice.stop()
        else:
            self.__event_handler.set(self.__channel.guild.id)
