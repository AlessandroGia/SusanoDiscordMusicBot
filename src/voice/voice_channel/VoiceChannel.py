from discord.ext.commands import Bot
from discord import Interaction
from src.voice.voice_state.VoiceState import VoiceState

import wavelink


class VoiceChannel:

    def __init__(self, bot: Bot) -> None:
        self.__states: dict[int, VoiceState] = {}
        self.__bot = bot

    def __get_voicestate(self, interaction: Interaction) -> VoiceState:
        return self.__states.setdefault(interaction.guild_id, VoiceState(self.__bot, self.__del_instance))

    def __del_instance(self, guild_id: int) -> None:
        print(guild_id, 'Deleted')
        ist = self.__states.pop(guild_id)
        del ist

    async def join(self, interaction: Interaction) -> None:
        voice = VoiceState(self.__bot, self.__del_instance)
        self.__states[interaction.guild.id] = voice
        await voice.join(interaction)

    async def play(self, interaction: Interaction, track: wavelink.YouTubeTrack, force: int) -> None:
        voice = self.__get_voicestate(interaction)
        await voice.play(interaction, track, force)

    async def leave(self, interaction: Interaction) -> None:
        voice = self.__get_voicestate(interaction)
        await voice.leave()

    async def next_song(self, interaction: Interaction) -> None:
        voice = self.__get_voicestate(interaction)
        await voice.next_song()

    async def toggle_loop(self, interaction: Interaction) -> bool:
        voice = self.__get_voicestate(interaction)
        return await voice.toggle_loop()

    async def toggle_pause(self, interaction: Interaction) -> bool:
        voice = self.__get_voicestate(interaction)
        return await voice.toggle_pause()

    async def reset(self, interaction: Interaction) -> None:
        voice = self.__get_voicestate(interaction)
        return await voice.reset()

    async def queue(self, interaction: Interaction) -> []:
        voice = self.__get_voicestate(interaction)
        return await voice.list_queue()

    async def shuffle(self, interaction: Interaction) -> None:
        voice = self.__get_voicestate(interaction)
        await voice.shuffle()

    async def remove(self, interaction: Interaction, index: int) -> str:
        voice = self.__get_voicestate(interaction)
        return await voice.remove(index)
