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
    @staticmethod
    def __create_embed(track: wavelink.YouTubeTrack, author: commands.Context.author, nome: str, in_loop: bool = False, in_pause: bool = False) -> discord.Embed:

        state = []

        if in_pause:
            state.append('in pausa')
        if in_loop:
            state.append('in loop')

        state = ' - {}'.format(", ".join(state)) if state else ''

        in_live = '[IN LIVE]' if track.is_stream() else ''
        title = f'***{nome}: {in_live} ***'

        thumb = track.thumbnail if track.thumbnail else track.thumb

        if int(track.duration) < 86400:
            durata = str(datetime.timedelta(seconds=track.duration))
            if int(durata.split(":")[-3]) == 0:
                durata = durata.split(":")[1] + ":" + durata.split(":")[2]
        else:
            durata = ' - '

        embed = discord.Embed(title=title, description=f'> [{track.title}]({track.uri})', color=discord.Color.blurple())
        if track.author:
            embed.add_field(name="Autore:", value=f"***{track.author}***", inline=True)
        embed.add_field(name="Durata:", value=f"***{durata}***", inline=True)
        embed.set_thumbnail(url=thumb)
        embed.set_author(name="susano", icon_url="https://webcdn.hirezstudios.com/smite/god-icons/susano.jpg")
        embed.set_footer(text=author.name + state, icon_url=author.avatar.url)

        return embed

    def inRiproduzione(self, track: wavelink.YouTubeTrack, author: commands.Context.author, in_loop: bool = False, in_pause: bool = False) -> discord.Embed:
        return self.__create_embed(track, author, "Riproducendo", in_loop=in_loop, in_pause=in_pause)

    def inCoda(self, track: wavelink.YouTubeTrack, author: commands.Context.author) -> discord.Embed:
        return self.__create_embed(track, author, "Aggiunta alla coda")
