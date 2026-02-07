import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os # <--- הוספנו את זה

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

yt_dlp.utils.bug_reports_message = lambda *args, **kwargs: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.command(name='play')
async def play(ctx, *, url):
    if not ctx.author.voice:
        await ctx.send("אתה חייב להיות בחדר קול!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            if voice_channel.is_playing():
                voice_channel.stop()
            voice_channel.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'🎵 מנגן כעת: **{player.title}**')
        except Exception as e:
            await ctx.send("שגיאה בניגון השיר.")
            print(e)

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹ נעצר.")

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

# שינוי קריטי ל-Railway: קריאת הטוקן מהסביבה
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("Error: DISCORD_TOKEN not found in environment variables")
