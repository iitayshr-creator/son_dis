import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import imageio_ffmpeg # <--- הטריק שלנו

# הגדרות בסיסיות
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# תיקון באגים של יוטיוב
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

# שימוש ב-FFmpeg הפנימי
ffmpeg_executable = imageio_ffmpeg.get_ffmpeg_exe()
print(f"✅ FFmpeg loaded from: {ffmpeg_executable}")

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
        
        # כאן אנחנו משתמשים ב-exe שהורדנו אוטומטית
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_executable, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.command(name='play')
async def play(ctx, *, url):
    if not ctx.author.voice:
        await ctx.send("כנס לחדר קול קודם!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)

    voice_channel = ctx.message.guild.voice_client

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            if voice_channel.is_playing():
                voice_channel.stop()
            voice_channel.play(player, after=lambda e: print(f'Error: {e}') if e else None)
            await ctx.send(f'🎵 מנגן: **{player.title}**')
        except Exception as e:
            await ctx.send(f"שגיאה: {e}")
            print(e)

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("עצרתי.")

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

# הרצה
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("Error: No Token Found!")
