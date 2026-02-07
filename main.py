import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio

# הגדרות בסיסיות
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# הגדרות מוזיקה
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'✅ הבוט {bot.user.name} מוכן ומחובר!')

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ אתה חייב להיות בחדר קולי!")
    
    vc = ctx.voice_client or await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
            url = info['url']
        
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        if vc.is_playing():
            vc.stop()
        vc.play(source)
        await ctx.send(f"🎶 מנגן עכשיו: **{info['title']}**")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 להתראות!")

# משיכת הטוקן מהגדרות Railway
bot.run(os.getenv('TOKEN'))
