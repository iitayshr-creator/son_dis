import discord
from discord.ext import commands
import yt_dlp
import asyncio

# --- הגדרות הבוט ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# כאן מגדירים את הקידומת לבוט (למשל !play)
bot = commands.Bot(command_prefix='!', intents=intents)

# --- הגדרות יוטיוב ו-FFmpeg ---
yt_dlp.utils.bug_reports_message = lambda: ''

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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    # הוספת reconnect חשובה כדי למנוע ניתוקים באמצע שיר
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
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# --- אירועים ופקודות ---

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.command(name='play', help='מנגן שיר מיוטיוב')
async def play(ctx, *, url):
    """
    פקודה לניגון שיר.
    שימוש: !play <שם שיר או קישור>
    """
    if not ctx.author.voice:
        await ctx.send("אתה חייב להיות בחדר קול כדי להשמיע מוזיקה!")
        return

    channel = ctx.author.voice.channel

    # הצטרפות לחדר אם הבוט לא שם
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
            await ctx.send("קרתה שגיאה בניסיון לנגן את השיר.")
            print(e)

@bot.command(name='stop', help='עוצר את המוזיקה')
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹ המוזיקה נעצרה.")
    else:
        await ctx.send("שום דבר לא מתנגן כרגע.")

@bot.command(name='leave', help='מוציא את הבוט מהחדר')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 יצאתי מהחדר.")
    else:
        await ctx.send("אני לא מחובר לחדר קול.")

# --- הרצת הבוט ---
# החלף את 'YOUR_TOKEN_HERE' בטוקן האמיתי שלך מפורטל המפתחים של דיסקורד
bot.run('YOUR_TOKEN_HERE')
