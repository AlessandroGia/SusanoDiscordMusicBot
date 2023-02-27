from typing import Callable

from discord import Interaction, ext, TextChannel, Message

import asyncio
import wavelink

import logging


from discord import Embed

from src.cogs.Music.event.EventHandler import EventHandler
from src.embed.Embed import Song
from src.exceptions.QueueException import NoTracksInQueueError, OutOfIndexQueue
from src.exceptions.TrackPlayerExceptions import *
from src.voice.voice_state.timeouts.TimeoutMembers import TimeoutMembers
from src.voice.voice_state.timeouts.TimeoutPause import TimeoutPause

from random import randint as r
from threading import Lock


class VoiceState:

    TIMEOUT_WAIT_FOR_A_SONG = (600)

    def __init__(self, bot: ext.commands.Bot, del_instance: Callable) -> None:
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
        self.bot: ext.commands.Bot = bot
        self.__del_instance: Callable = del_instance
        self.__embed: Song = Song()
        self.__lock_queue: Lock = Lock()

        self.voice: wavelink.Player = None

        self.__event_handler: EventHandler = self.bot.event_handler

        self.__audio_player: asyncio.Task = None

        self.__timeout_in_pause: TimeoutPause = TimeoutPause(self)
        self.__timeout_members: TimeoutMembers = TimeoutMembers(self)

        self.__queue_tracks: wavelink.WaitQueue = wavelink.WaitQueue()

        self.__current_track: wavelink.YouTubeTrack = None
        self.__current_interaction: Interaction = None

        self.__loop: bool = False
        self.__pause: bool = False

        self.__interaction_flag: bool = False

        self.__channel: TextChannel = None
        self.__channel_embed: Message = None

    def __reset(self):
        self.voice: wavelink.Player = None
        self.__event_handler: EventHandler = self.bot.event_handler
        self.__audio_player: asyncio.Task = None
        self.__timeout_in_pause: TimeoutPause = TimeoutPause(self)
        self.__timeout_members: TimeoutMembers = TimeoutMembers(self)
        self.__queue_tracks: wavelink.WaitQueue = wavelink.WaitQueue()
        self.__current_track: wavelink.YouTubeTrack = None
        self.__current_interaction: Interaction = None
        self.__loop: bool = False
        self.__pause: bool = False
        self.__interaction_flag: bool = False
        self.__channel: TextChannel = None
        self.__channel_embed: Message = None

    async def join(self, interaction: Interaction) -> None:
        self.voice: wavelink.Player = await interaction.user.voice.channel.connect(
            self_deaf=True,
            cls=wavelink.Player
        )
        self.__channel = interaction.channel
        self.__event_handler.add_event(self.__channel.guild.id)
        self.__audio_player = self.bot.loop.create_task(self.__audio_player_coro())
        await self.__timeout_members.run()

    async def play(self, interaction: Interaction, track: wavelink.YouTubeTrack, force: int) -> None:
        if force:
            self.__interaction_flag = True
            self.__current_interaction = interaction
            await self.__force_track(track)
        else:
            if self.__current_track:
                await interaction.response.send_message(
                    embed=self.__embed.inCoda(track, interaction.user)
                )
            else:
                self.__interaction_flag = True
                self.__current_interaction = interaction
            self.__add_to_queue(track)

    async def __force_track(self, track: wavelink.YouTubeTrack):
        self.__queue_tracks.put_at_front(track)
        if self.__current_track:
            await self.voice.stop()

    async def leave(self) -> None:
        if self.voice.is_playing() or self.voice.is_paused():
            await self.voice.stop()
        await self.voice.disconnect()
        await self.__exit()

    async def remove(self, index: int) -> str:
        if self.__queue_empty():
            raise NoTracksInQueueError
        with self.__lock_queue:
            if index < self.__queue_tracks.count:
                item = self.__queue_tracks.__getitem__(index)
                self.__queue_tracks.__delitem__(index)
                return item.title
            else:
                raise OutOfIndexQueue

    async def shuffle(self) -> None:
        if self.__queue_empty():
            raise NoTracksInQueueError
        with self.__lock_queue:
            for i in range(self.__queue_tracks.count):
                index = i
                while index == i and i != self.__queue_tracks.count - 1:
                    index = r(i, self.__queue_tracks.count - 1)
                track = self.__queue_tracks.__getitem__(index)
                self.__queue_tracks.__delitem__(index)
                self.__queue_tracks.put(track)

    async def list_queue(self) -> []:
        if self.__queue_empty():
            raise NoTracksInQueueError
        return self.__queue_tracks.count, self.__queue_tracks.__iter__()

    def __add_to_queue(self, track: wavelink.YouTubeTrack) -> None:
        self.__queue_tracks.put(track)

    def __queue_empty(self) -> bool:
        return self.__queue_tracks.is_empty

    def __clear_queues(self) -> None:
        self.__queue_tracks.clear()

    async def __exit(self) -> None:
        if self.__audio_player:
            self.__audio_player.cancel()
        if self.__timeout_members:
            self.__timeout_members.cancel()
        if self.__timeout_in_pause:
            self.__timeout_in_pause.cancel()
        self.__del_instance(self.__channel.guild.id)
        self.__reset()

    async def toggle_loop(self) -> bool:
        if not self.__current_track:
            raise NoCurrentTrackError
        self.__loop = not self.__loop
        await self.__update_current_song()
        return self.__loop

    async def toggle_pause(self) -> bool:
        if not self.__current_track:
            raise NoCurrentTrackError
        if self.__pause:
            if self.voice.is_paused():
                self.__timeout_in_pause.set()
                await self.voice.resume()
                self.__timeout_in_pause.cancel()
        elif not self.__pause:
            if self.voice.is_playing():
                await self.voice.pause()
                self.__timeout_in_pause.clear()
                await self.__timeout_in_pause.run()
        self.__pause = not self.__pause
        await self.__update_current_song()
        return self.__pause

    async def reset(self):
        if not self.__current_track:
            raise NoCurrentTrackError
        self.__clear_queues()
        self.__loop = False
        if self.voice.is_playing() or self.voice.is_paused():
            await self.voice.stop()
        if self.__pause:
            await self.toggle_pause()

    async def next_song(self) -> None:
        if not self.__current_track:
            raise NoCurrentTrackError
        await self.voice.stop()

    async def __audio_player_coro(self) -> None:
        while True:
            if self.__current_interaction:
                self.__event_handler.clear(self.__channel.guild.id)
            self.__current_track = None
            try:
                print(' - Aspettando la canzone dalla coda')
                with self.__lock_queue:
                    self.__current_track = await asyncio.wait_for(self.__queue_tracks.get_wait(), timeout=self.TIMEOUT_WAIT_FOR_A_SONG)
                print('Canzone presa dalla coda')
            except asyncio.TimeoutError:
                await self.leave()
                return None
            else:
                try:
                    await self.__send_current_song()
                    await self.voice.play(self.__current_track)
                    if self.__pause:
                        await self.voice.pause()
                    print(' - Aspettando la fine della canzone')
                    await self.__event_handler.wait(self.__channel.guild.id)
                    self.__interaction_flag = False
                    print('Canzone Finita')
                    if self.__loop:
                        self.__add_to_queue(self.__current_track)
                except Exception as e:
                    print('Errore 2:', e)
                    await self.__clean_up_stuck()

    def __embed_in_riproduzione(self) -> Embed:
        return self.__embed.inRiproduzione(
            self.__current_track, self.__current_interaction.user, in_loop=self.__loop, in_pause=self.__pause
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
        if self.voice.is_playing() or self.voice.is_paused():
            await self.voice.stop()
        else:
            self.__event_handler.set(self.__channel.guild.id)
