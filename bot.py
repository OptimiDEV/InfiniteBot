import disnake
from disnake.ext import commands, tasks
import datetime
import google.generativeai as genai
import yt_dlp
from better_profanity import profanity

# --- CONFIGURATION ---
TOKEN = "Your discord token, get it from discord.dev"
GEMINI_API_KEY = "Your gemini API key, get it from https://aistudio.google.com/apikey"

WELCOME_CHANNEL_ID = 1348229655538307083
LEAVE_CHANNEL_ID = 1348229655538307083
YOUTUBE_CHANNEL_ID = "UCnUxOyg8dCP4bUO7vH5GEBg"
UPLOAD_ANNOUNCE_CHANNEL = 1397123820778819695
QOTD_CHANNEL_ID = 1362713576292356137
REPORT_LOG_CHANNEL_ID = 1349380092337459250
UPLOAD_PING_ROLE_ID = 1397124023133016135  # Replace with real role ID
YOUR_GUILD_ID = 1320418271375265813        # Replace with your guild ID

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
# InfiniteBot uses gemini 2.0 flash as its standard model, you can find other models on https://ai.google.dev/gemini-api/docs/models
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Automod setup
profanity.load_censor_words()  # Use built-in wordlist

# For YouTube monitoring
last_video_id = None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    # check_youtube.start()
    send_qotd.start()

# --- WELCOME / LEAVE MESSAGES ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    await channel.send(f"👋 Welcome {member.mention} to the server!")

@bot.slash_command(name="qotdnow", description="Post the QOTD now")
@commands.has_permissions(administrator=True)
async def qotd_now(ctx):
    """Force post a new Question of the Day from Gemini."""
    await ctx.send("📨 Fetching a new Question of the Day...")
    prompt = "Give a unique, thought-provoking, short question of the day for a Discord community."
    response = gemini_model.generate_content(prompt)
    question = response.text.strip()
    channel = bot.get_channel(QOTD_CHANNEL_ID)
    await channel.send(f"🧠 **Question of the Day:**\n> {question}")
    await ctx.send("✅ Posted to the QOTD channel.")


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LEAVE_CHANNEL_ID)
    await channel.send(f"{member.name} has left the server :(")
  
# Disabled because it's broken
# --- YOUTUBE UPLOAD CHECK ---
#@tasks.loop(minutes=5)
#async def check_youtube():
#    global last_video_id
#    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
#    url = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}/videos"
#
#    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#        info = ydl.extract_info(url, download=False)
#        latest = info['entries'][0]
#        video_id = latest['id']
#
#        if video_id != last_video_id:
#            last_video_id = video_id
#            video_url = f"https://youtu.be/{video_id}"
#            channel = bot.get_channel(UPLOAD_ANNOUNCE_CHANNEL)
#            guild = bot.get_guild(YOUR_GUILD_ID)
#            role = guild.get_role(UPLOAD_PING_ROLE_ID)
#            await channel.send(f"{role.mention} New video uploaded: {video_url}")


# --- DAILY QOTD FROM GEMINI ---
@tasks.loop(time=datetime.time(hour=0, minute=0, second=0))
async def send_qotd():
    prompt = "Give a unique, thought-provoking, short question of the day for a Discord community without anything else, just say the question of the day."
    response = gemini_model.generate_content(prompt)
    question = response.text.strip()
    channel = bot.get_channel(QOTD_CHANNEL_ID)
    await channel.send(f"🧠 **Question of the Day:**\n> {question}")

# --- REACTION REPORTING ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name not in ["🏴", "🔨"]:
        return

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)

    if message.author.bot or user.bot:
        return

    reason = "Rule-breaking" if payload.emoji.name == "🏴" else "Racism/Homophobia"
    log_channel = bot.get_channel(REPORT_LOG_CHANNEL_ID)
    
    embed = disnake.Embed(title="🚨 Message Reported", color=disnake.Color.red())
    embed.add_field(name="Reporter", value=user.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Message Author", value=message.author.mention)
    embed.add_field(name="Content", value=message.content or "[No text]")
    embed.add_field(name="Channel", value=channel.mention)
    embed.add_field(name="Jump to Message", value=f"[Click Here]({message.jump_url})", inline=False)

    await log_channel.send(embed=embed)

# --- AUTOMOD WITH better-profanity ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if profanity.contains_profanity(message.content):
        await message.delete()
        await message.channel.send(
            f"{message.author.mention} 🚫 Your message was removed for inappropriate language.",
            delete_after=5
        )
        log_channel = bot.get_channel(REPORT_LOG_CHANNEL_ID)
        embed = disnake.Embed(title="🔒 Automod Deletion", color=disnake.Color.orange())
        embed.add_field(name="User", value=message.author.mention)
        embed.add_field(name="Content", value=message.content or "[No text]", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention)
        await log_channel.send(embed=embed)
        return

    await bot.process_commands(message)

# --- RUN BOT ---
bot.run(TOKEN)
