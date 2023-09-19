import discord
import wavelink
import datetime
from discord.ext import commands
from discord import Colour, Embed as embed
from wavelink.ext import spotify


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
    def __create_youtube_embed(self, track: wavelink.YouTubeTrack, author: commands.Context.author, action: str, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False, source: bool = False) -> discord.Embed:

        state = self.__set_state(in_loop, in_loop_all, in_pause)

        source = 'da Youtube' if source else ''

        in_live = '[IN LIVE]' if track.is_stream else ''
        title = f'***{action} {source}: {in_live} ***' + state

        thumb = track.thumbnail if track.thumbnail else track.thumb

        durata = self.__millisec_to_min(track.duration)

        embed = discord.Embed(title=title, description=f'> [{track.title}]({track.uri})', color=discord.Color.blurple())
        if track.author:
            embed.add_field(name="Autore:", value=f"***{track.author}***", inline=True)
        embed.add_field(name="Durata:", value=f"***{durata}***", inline=True)
        embed.set_thumbnail(url=thumb)
        embed.set_author(name="susano", icon_url="https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg")
        embed.set_footer(text=author.name, icon_url=author.avatar.url)

        return embed

    def __create_spotify_embed(self, track: spotify.SpotifyTrack, author: commands.Context.author, action: str, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False, source: bool = False) -> discord.Embed:

        state = self.__set_state(in_loop, in_loop_all, in_pause)

        source = 'da Spotify' if source else ''

        title = f'***{action} {source}: ***' + state

        durata = self.__millisec_to_min(track.duration)

        embed = discord.Embed(title=title, description=f'> {track.title}', color=discord.Color.yellow())
        if track.artists:
            embed.add_field(name="Artista:" if len(track.artists) == 1 else "Artisti:", value=' - '.join([f"***{track_}***" for track_ in track.artists]), inline=True)
        embed.add_field(name="Durata:", value=f"***{durata}***", inline=True)
        embed.add_field(name="Album:", value=f"***{track.album}***", inline=False)
        embed.set_thumbnail(url=track.images[0])
        embed.set_author(name="susano", icon_url="https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg")
        embed.set_footer(text=author.name, icon_url=author.avatar.url)

        return embed

    def __millisec_to_min(self, ms: int) -> str:
        if int(ms) < (24 * 60 * 60 * 1000):
            durata = str(datetime.timedelta(milliseconds=ms))
            if int(durata.split(":")[-3]) == 0:
                durata = str(round(float(durata.split(":")[1]))) + ":" + str(round(float(durata.split(":")[2])))
        else:
            durata = ' - '

        return durata

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

    def inRiproduzione(self, track: wavelink.YouTubeTrack | spotify.SpotifyTrack, author: commands.Context.author, in_loop: bool = False, in_loop_all: bool = False, in_pause: bool = False) -> discord.Embed:
        if isinstance(track, wavelink.YouTubeTrack):
            return self.__create_youtube_embed(track, author, "Riproducendo", in_loop=in_loop, in_loop_all=in_loop_all, in_pause=in_pause, source=True)
        elif isinstance(track, spotify.SpotifyTrack):
            return self.__create_spotify_embed(track, author, "Riproducendo", in_loop=in_loop, in_loop_all=in_loop_all, in_pause=in_pause, source=True)

    def inCoda(self, track: wavelink.YouTubeTrack | spotify.SpotifyTrack, author: commands.Context.author) -> discord.Embed:
        if isinstance(track, wavelink.YouTubeTrack):
            return self.__create_youtube_embed(track, author, "Aggiunta alla coda")
        elif isinstance(track, spotify.SpotifyTrack):
            return self.__create_spotify_embed(track, author, "Aggiunta alla coda")
