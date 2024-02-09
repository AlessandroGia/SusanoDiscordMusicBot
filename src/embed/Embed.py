import discord
import wavelink
import datetime
from discord.ext import commands
from discord import Colour, Embed as embed


class Embed:
    def __init__(self) -> None:
        self.__name_bot = "Susano"
        self.__icon_url = "https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg"
        pass

    def error(self, error: str = " ") -> embed:
        emb = embed(title=" ", description="***"+error+"***", colour=Colour.red())
        emb.set_author(name=self.__name_bot, icon_url=self.__icon_url)
        return emb

    def embed(self, mess: str = " ", title: str = " ", footer: str = " ") -> embed:
        emb = embed(title=title, description=mess.replace(", Default", ""), colour=Colour.blue())
        emb.set_author(name=self.__name_bot, icon_url=self.__icon_url)
        emb.set_footer(text=footer)
        return emb


class Song:
    def __create_youtube_embed(self, track: wavelink.Search, author: commands.Context.author, action: str, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False, source: bool = False) -> discord.Embed:

        state = self.__set_state(in_loop, in_loop_all, in_pause)

        source = ' da Youtube' if source else ''

        in_live = '[IN LIVE]' if track.is_stream else ''
        title = f'***{action}{source}: {in_live} ***' + state

        thumb = track.artwork

        durata = self.__millisec_to_min(track.length)

        embed = discord.Embed(title=title, description=f'> [{track.title}]({track.uri})', color=discord.Color.blurple())
        embed.add_field(name="Autore:", value=f"***{track.author}***", inline=True) if track.author else None
        embed.add_field(name="Durata:", value=f"***{durata}***", inline=True)
        embed.set_thumbnail(url=thumb)
        embed.set_author(name="susano", icon_url="https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg")
        embed.set_footer(text=author.name, icon_url=author.avatar.url)

        return embed

    def __create_youtube_playlist_embed(self, playlist: wavelink.Playlist, author: commands.Context.author, action: str, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False, source: bool = False) -> discord.Embed:

        state = self.__set_state(in_loop, in_loop_all, in_pause)

        source = ' da Youtube' if source else ''

        title = f'***Playlist {action}{source}: ***' + state

        embed = discord.Embed(title=title, description=f'> {playlist.name}', color=discord.Color.blurple())
        embed.add_field(name="Autore:", value=f"***{playlist.author}***", inline=True) if playlist.author else None
        embed.add_field(name="Tracce:", value=f"***{len(playlist.tracks)}***", inline=True) if playlist.tracks else None
        embed.set_thumbnail(url=playlist.artwork) if playlist.artwork else None
        embed.set_author(name="susano", icon_url="https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg")
        embed.set_footer(text=author.name, icon_url=author.avatar.url)

        return embed

    def __millisec_to_min(self, ms: int) -> str:
        if int(ms) < (24 * 60 * 60 * 1000):
            secs = ms // 1000
            min = secs // 60
            sec = secs % 60
            return f"{min:02d}:{sec:02d}"
        else:
            return ' - '

    def __set_state(self, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False) -> str:

        state = []

        if in_pause:
            state.append('🔇')
        if in_loop:
            state.append('🔂')
        if in_loop_all:
            state.append('🔁')

        state = '  {}'.format("  ".join(state)) if state else ''

        return state

    def inRiproduzione(self, track: wavelink.Search, author: commands.Context.author, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False) -> discord.Embed:
        return self.__create_youtube_embed(track, author, "Riproducendo", in_loop=in_loop, in_loop_all=in_loop_all, in_pause=in_pause, source=True)

    def inCoda(self, track: wavelink.Search, author: commands.Context.author) -> discord.Embed:
        if isinstance(track, wavelink.Playlist):
            return self.__create_youtube_playlist_embed(track, author, "aggiunta alla coda")
        else:
            return self.__create_youtube_embed(track, author, "Aggiunta alla coda")

