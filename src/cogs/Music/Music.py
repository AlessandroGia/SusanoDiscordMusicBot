from discord import Object, Interaction, app_commands, ext

from src.exceptions.Generic import Generic
from src.exceptions.QueueException import *
from src.exceptions.TrackPlayerExceptions import *
from src.exceptions.VoiceChannelExceptions import *
from src.checks.VoiceChannelChecks import check_voice_channel
from src.embed.Embed import Embed
from src.utils.Utils import search_url

import wavelink
from discord.ext import commands

from wavelink.ext import spotify
from src.voice.voice_channel.VoiceChannel import VoiceChannel

import discord


class Music(ext.commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.__embed: Embed = Embed()
        self.__vc: VoiceChannel = bot.vc

    # Command: Reset #

    @app_commands.command(
        name='reset',
        description='Cancella tutta la coda',
    )
    @check_voice_channel()
    async def reset(self, interaction: Interaction):
        await self.__vc.reset(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '**Coda cancellata**'
            ),
            delete_after=3
        )

    # Command: Pause #

    @app_commands.command(
        name='pause',
        description='Mette in pausa/riprende la canzone corrente'
    )
    @check_voice_channel()
    async def pause(self, interaction: Interaction):
        pause = await self.__vc.toggle_pause(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '**Canzone messa in pausa**' if pause else '**Canzone ripresa**'
            ),
            delete_after=3
        )

    # Command: Skip #

    @app_commands.command(
        name='skip',
        description='Salta la canzone corrente'
    )
    @check_voice_channel()
    async def skip(self, interaction: Interaction):
        await self.__vc.skip(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '**Canzone saltata**'
            ),
            delete_after=3
        )

    # Command: Loop #

    @app_commands.command(
        name='loop_all',
        description='Attiva/disattiva il loop della coda'
    )
    @check_voice_channel()
    async def loop_all(self, interaction: Interaction):
        loop = await self.__vc.toggle_loop_all(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '**Loop della coda attivato**' if loop else '**Loop disattivato**'
            ),
            delete_after=3
        )

    @app_commands.command(
        name='loop',
        description='Attiva/disattiva il loop della canzone corrente'
    )
    @check_voice_channel()
    async def loop(self, interaction: Interaction):
        loop = await self.__vc.toggle_loop(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '**Loop attivato**' if loop else '**Loop disattivato**'
            ),
            delete_after=3
        )

    # Command: Join #

    @app_commands.command(
        name='join',
        description='Fa entrare il bot nel canale vocale'
    )
    @check_voice_channel()
    async def join(self, interaction: Interaction):
        try:
            await self.__vc.join(interaction)
        except Exception as e:
            print(e)
        await interaction.response.send_message(embed=self.__embed.embed(
            "**Bot entrato in** : _{}_".format(interaction.user.voice.channel)
            ),
            delete_after=5
        )

    # Command: Leave #

    @app_commands.command(
        name='leave',
        description='Fa uscire il bot dal canale vocale'
    )
    @check_voice_channel()
    async def leave(self, interaction: Interaction):
        await self.__vc.leave(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            "**Bot Uscito da** : _{}_".format(interaction.user.voice.channel)
            ),
            delete_after=5
        )

    # Command: Play #

    @app_commands.command(
        name='play',
        description='Riproduce una canzone',
    )
    @app_commands.describe(
        search='Url o Nome della canzone da cercare',
        force='Forza la riproduzione della canzone',
        source='Piattaforma in cui cercare la canzone'
    )
    @app_commands.choices(
        source=[
            app_commands.Choice(name='Youtube', value='youtube'),
            app_commands.Choice(name='Spotify', value='spotify')
        ],
        force=[
            app_commands.Choice(name='Si', value=1),
            app_commands.Choice(name='No', value=0)
        ]
    )
    @check_voice_channel()
    async def play(self, interaction: Interaction, search: str, force: int = 0, source: str = 'youtube'):
        if source == 'youtube':
            search = search_url(search)
            tracks: list[wavelink.YouTubeTrack] = await wavelink.YouTubeTrack.search(search)
            if not tracks:
                raise TrackNotFoundError
            track: wavelink.YouTubeTrack = tracks[0]

        elif source == 'spotify':
            decoded = spotify.decode_url(search)
            if not decoded or decoded['type'] is not spotify.SpotifySearchType.track:
                raise InvalidSpotifyURL  # Only Spotify Track URLs are valid.

            tracks: list[spotify.SpotifyTrack] = await spotify.SpotifyTrack.search(search)

            if not tracks:
                raise InvalidSpotifyURL  # This does not appear to be a valid Spotify URL.
            track: spotify.SpotifyTrack = tracks[0]
            print(track)
        await self.__vc.play(interaction, track, force)

    # Command: Queue #

    @app_commands.command(
        name='queue',
        description='Mostra le prime 10 canzoni in coda'
    )
    @check_voice_channel()
    async def queue(self, interaction: Interaction):
        num_tracks, queue = await self.__vc.queue(interaction)
        i, body = 1, []
        for track in queue:
            body.append(f'***{i}***. {track}')
            i += 1
        await interaction.response.send_message(embed=self.__embed.embed(
                '\n'.join(body), f'Canzoni in coda: {num_tracks}'
            )
        )

    # Command: Shuffle #

    @app_commands.command(
        name='shuffle',
        description='Mischia la coda'
    )
    @check_voice_channel()
    async def shuffle(self, interaction: Interaction):
        await self.__vc.shuffle(interaction)
        await interaction.response.send_message(embed=self.__embed.embed(
            '***Coda Mischiata***'
            ),
            delete_after=5
        )

    # Command: Remove #

    @app_commands.command(
        name='remove',
        description='Rimuove una canzone dalla coda'
    )
    @app_commands.describe(
        index='Specifica la posizione della canzone nella coda. Vedi: /queue'
    )
    @check_voice_channel()
    async def remove(self, interaction: Interaction, index: int):
        track = await self.__vc.remove(interaction, index - 1)
        await interaction.response.send_message(embed=self.__embed.embed(
            f'*{track}* ***rimossa***'
            ),
            delete_after=5
        )

    # Checks #

    @loop_all.error
    @shuffle.error
    @remove.error
    @queue.error
    @reset.error
    @pause.error
    @skip.error
    @loop.error
    @play.error
    async def play_error(self, interaction: Interaction, error):
        if isinstance(error, UserNonConnessoError):
            await interaction.response.send_message(embed=self.__embed.error("Non sei connesso a nessun canale vocale"), ephemeral=True, delete_after=5)
        elif isinstance(error, BotNonPresenteError):
            await interaction.response.send_message(embed=self.__embed.error("Il bot non e' connesso a nessun canale vocale"), ephemeral=True, delete_after=5)
        elif isinstance(error, UserNonStessoCanaleBotError):
            await interaction.response.send_message(embed=self.__embed.error("Non sei nello stesso canale del bot"), ephemeral=True, delete_after=5)
        elif isinstance(error, NoTracksInQueueError):
            await interaction.response.send_message(embed=self.__embed.error("Non ci sono canzoni in coda"),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, NoCurrentTrackError):
            await interaction.response.send_message(embed=self.__embed.error("Non c'e' nessuna canzone in riproduzione"),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, TrackNotFoundError):
            await interaction.response.send_message(embed=self.__embed.error("Canzone non trovata"),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, OutOfIndexQueue):
            await interaction.response.send_message(embed=self.__embed.error('Selezione errata'),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, AlreadyLoop):
            await interaction.response.send_message(embed=self.__embed.error('Il loop e\' gia\' attivo'),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, AlreadyLoopAll):
            await interaction.response.send_message(embed=self.__embed.error('Il loop della coda e\' gia\' attivo'),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, InvalidSpotifyURL):
            await interaction.response.send_message(embed=self.__embed.error('URL di Spotify non valido'),
                                                    ephemeral=True, delete_after=5)
        elif isinstance(error, Generic):
            await interaction.response.send_message(embed=self.__embed.error("Si e' verificato un errore"),
                                                    ephemeral=True, delete_after=5)

    @leave.error
    async def leave_error(self, interaction: Interaction, error):
        if isinstance(error, UserNonConnessoError):
            await interaction.response.send_message(embed=self.__embed.error("Non sei connesso a nessun canale vocale"), ephemeral=True, delete_after=5)
        elif isinstance(error, BotNonPresenteError):
            await interaction.response.send_message(embed=self.__embed.error("Il bot non e' connesso a nessun canale vocale"), ephemeral=True, delete_after=5)
        elif isinstance(error, UserNonStessoCanaleBotError):
            await interaction.response.send_message(embed=self.__embed.error("Non sei nello stesso canale del bot"), ephemeral=True, delete_after=5)

    @join.error
    async def join_error(self, interaction: Interaction, error):
        if isinstance(error, UserNonConnessoError):
            await interaction.response.send_message(embed=self.__embed.error("Non sei connesso a nessun canale vocale"), ephemeral=True, delete_after=5)
        elif isinstance(error, BotGiaConnessoError):
            await interaction.response.send_message(embed=self.__embed.error("Bot gia' connesso"), ephemeral=True, delete_after=5)


async def setup(bot: ext.commands.Bot):
    await bot.add_cog(Music(bot), guilds=[Object(id=928785387239915540)])
