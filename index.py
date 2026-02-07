import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import sys

# 1. הגדרות בסיסיות ו-Intents
intents = discord.Intents.default()
intents.message_content = True  # חשוב: וודא שזה דלוק ב-Developer Portal
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. הגדרות FFmpeg ו-YT-DLP
# בדיקה אם אנחנו על ווינדוס (בשביל ה-ffmpeg.exe) או על שרת Railway
IS_WINDOWS = sys.platform == "win32"
FFMPEG_EXE = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

@bot.event
async def on_ready():
    print(f'---')
    print(f'הבוט {bot.user.name} מחובר ומוכן לעבודה!')
    print(f'מערכת הפעלה מזהה: {"Windows" if IS_WINDOWS else "Linux/Railway"}')
    print(f'---')

# 3. פקודות המוזיקה
@bot.command(name="play", aliases=["p"])
async def play(ctx, *, search: str):
    """מנגן שיר מיוטיוב לפי לינק או שם שיר"""
    
    # בדיקה אם המשתמש בחדר קולי
    if not ctx.author.voice:
        return await ctx.send("❌ אתה חייב להיות בחדר קולי כדי לנגן מוזיקה!")

    # חיבור לחדר הקולי
    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    async with ctx.typing():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                # חיפוש השיר (תומך גם בלינקים וגם בשמות)
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url2 = info['url']
                title = info['title']
        except Exception as e:
            return await ctx.send(f"❌ שגיאה במציאת השיר: {e}")

    # עצירת שיר קודם אם רץ
    if vc.is_playing():
        vc.stop()

    # יצירת מקור השמע
    try:
        source = discord.FFmpegPCMAudio(url2, executable=FFMPEG_EXE, **FFMPEG_OPTIONS)
        vc.play(source, after=lambda e: print(f'סיים לנגן: {e}') if e else None)
        await ctx.send(f"🎶 מנגן עכשיו: **{title}**")
    except Exception as e:
        await ctx.send(f"❌ שגיאה בהפעלת הנגן: {e}")

@bot.command(name="stop", aliases=["leave", "s"])
async def stop(ctx):
    """מפסיק את המוזיקה ויוצא מהחדר"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 להתראות!")
    else:
        await ctx.send("❓ אני לא נמצא בחדר קולי.")

# 4. הרצת הבוט
# ב-Railway נשתמש במשתנה סביבה, בבית אפשר לשים את הטוקן ישירות
TOKEN = os.getenv('DISCORD_TOKEN') or 'כאן_שים_את_הטוקן_שלך_לבדיקה_בבית'

if __name__ == "__main__":
    bot.run(TOKEN)
