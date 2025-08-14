
import io
import datetime
import sqlite3
import disnake
from disnake.ext import commands, tasks
from better_profanity import profanity
from google import genai
from google.genai import types


# --- CONFIGURATION ---
TOKEN = "Your discord token, get it from discord.dev"
GEMINI_API_KEY = "Your gemini API key, get it from https://aistudio.google.com/apikey"

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SQLite database ---
conn = sqlite3.connect("guild_settings.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    welcome_channel_id INTEGER,
    leave_channel_id INTEGER,
    qotd_channel_id INTEGER,
    report_log_channel_id INTEGER,
    moderation_enabled INTEGER DEFAULT 1,
    ai_enabled INTEGER DEFAULT 1
)
""")
conn.commit()

def get_guild_settings(guild_id):
    c.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,))
    row = c.fetchone()
    if row:
        return {
            "guild_id": row[0],
            "welcome_channel_id": row[1],
            "leave_channel_id": row[2],
            "qotd_channel_id": row[3],
            "report_log_channel_id": row[4],
            "moderation_enabled": bool(row[5]),
            "ai_enabled": bool(row[6])
        }
    else:
        c.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        return get_guild_settings(guild_id)

# --- Gemini setup ---
genai_client = genai.Client(api_key=GEMINI_API_KEY)
TEXT_MODEL = "gemini-2.0-flash"
profanity.load_censor_words()

# --- Individual Setup Commands ---
@bot.slash_command(description="Set welcome channel")
@commands.has_permissions(administrator=True)
async def setup_welcome(inter: disnake.CommandInteraction, channel: disnake.TextChannel = None):
    c.execute("UPDATE guild_settings SET welcome_channel_id=? WHERE guild_id=?", (channel.id if channel else None, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ Welcome channel set to {channel.mention if channel else 'disabled'}")

@bot.slash_command(description="Set leave channel")
@commands.has_permissions(administrator=True)
async def setup_leave(inter: disnake.CommandInteraction, channel: disnake.TextChannel = None):
    c.execute("UPDATE guild_settings SET leave_channel_id=? WHERE guild_id=?", (channel.id if channel else None, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ Leave channel set to {channel.mention if channel else 'disabled'}")

@bot.slash_command(description="Set QOTD channel")
@commands.has_permissions(administrator=True)
async def setup_qotd(inter: disnake.CommandInteraction, channel: disnake.TextChannel = None):
    c.execute("UPDATE guild_settings SET qotd_channel_id=? WHERE guild_id=?", (channel.id if channel else None, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ QOTD channel set to {channel.mention if channel else 'disabled'}")

@bot.slash_command(description="Set report log channel")
@commands.has_permissions(administrator=True)
async def setup_reportlog(inter: disnake.CommandInteraction, channel: disnake.TextChannel = None):
    c.execute("UPDATE guild_settings SET report_log_channel_id=? WHERE guild_id=?", (channel.id if channel else None, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ Report log channel set to {channel.mention if channel else 'disabled'}")

@bot.slash_command(description="Enable or disable moderation")
@commands.has_permissions(administrator=True)
async def setup_moderation(inter: disnake.CommandInteraction, enabled: bool):
    c.execute("UPDATE guild_settings SET moderation_enabled=? WHERE guild_id=?", (1 if enabled else 0, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ Moderation {'enabled' if enabled else 'disabled'}")

@bot.slash_command(description="Enable or disable AI mention replies")
@commands.has_permissions(administrator=True)
async def setup_ai(inter: disnake.CommandInteraction, enabled: bool):
    c.execute("UPDATE guild_settings SET ai_enabled=? WHERE guild_id=?", (1 if enabled else 0, inter.guild_id))
    conn.commit()
    await inter.send(f"✅ AI mention replies {'enabled' if enabled else 'disabled'}")

# --- Force QOTD ---
@bot.slash_command(description="Send today's Question of the Day manually")
@commands.has_permissions(administrator=True)
async def forceqotd(inter: disnake.CommandInteraction):
    settings = get_guild_settings(inter.guild_id)
    if not settings["qotd_channel_id"]:
        await inter.send("⚠ No QOTD channel set for this server.")
        return
    prompt = "Give a unique, thought-provoking question of the day for a Discord community."
    resp = genai_client.models.generate_content(
        model=TEXT_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(max_output_tokens=1000)
    )
    question = resp.candidates[0].content.text.strip()[:4000]
    channel = bot.get_channel(settings["qotd_channel_id"])
    if channel:
        await channel.send(f"**Question of the Day:**\n> {question}")
        await inter.send("✅ QOTD sent.", ephemeral=True)
    else:
        await inter.send("⚠ Could not find the QOTD channel.", ephemeral=True)

# --- Daily QOTD ---
@tasks.loop(time=datetime.time(hour=0, minute=0, second=0))
async def send_qotd():
    for guild in bot.guilds:
        settings = get_guild_settings(guild.id)
        if settings["qotd_channel_id"]:
            prompt = "Give a unique, thought-provoking question of the day for a Discord community."
            resp = genai_client.models.generate_content(
                model=TEXT_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(max_output_tokens=1000)
            )
            question = resp.candidates[0].content.text.strip()[:4000]
            channel = bot.get_channel(settings["qotd_channel_id"])
            if channel:
                await channel.send(f"**Question of the Day:**\n> {question}")

# --- Events ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    send_qotd.start()

@bot.event
async def on_message(message):
    if not message.guild or message.author.bot:
        return

    settings = get_guild_settings(message.guild.id)

    # Automod
    if settings["moderation_enabled"] and profanity.contains_profanity(message.content):
        await message.delete()
        await message.channel.send(
            f"{message.author.mention} 🚫 Inappropriate language detected.",
            delete_after=5
        )
        if settings["report_log_channel_id"]:
            embed = disnake.Embed(
                title="Automod Alert",
                color=disnake.Color.orange()
            )
            embed.add_field(name="User", value=message.author.mention)
            embed.add_field(name="Content", value=message.content or "[No content]", inline=False)
            await bot.get_channel(settings["report_log_channel_id"]).send(embed=embed)
        return

    # AI Mention
    if settings["ai_enabled"] and bot.user in message.mentions:
        user_query = (
            message.content
            .replace(f"<@{bot.user.id}>", "")
            .replace(f"<@!{bot.user.id}>", "")
            .strip()
        )
        if not user_query:
            await message.reply("You mentioned me, but didn’t ask anything.")
            return

        system_rules = (
            "You are a helpful and respectful AI assistant. "
            "Never use profanity, sexual content, or slurs. "
            "Keep replies polite, concise, and under 4000 characters."
        )
        try:
            resp = genai_client.models.generate_content(
                model=TEXT_MODEL,
                contents=[system_rules, user_query],
                config=types.GenerateContentConfig(
                    max_output_tokens=1000,
                    response_modalities=[types.Modality.TEXT]
                )
            )
            text_parts = [
                part.text.strip()
                for part in resp.candidates[0].content.parts
                if part.text
            ]
            final_text = " ".join(text_parts)[:4000]

            if profanity.contains_profanity(final_text):
                await message.reply(
                    "Apparently, our AI tried to curse — this is strictly blocked by the "
                    "developer team of InfiniteBot.\n\nThink this is wrong? "
                    "Open an issue on https://github.com/OptimiDEV/InfiniteBot/issues"
                )
            else:
                await message.reply(final_text)

        except Exception as e:
            await message.reply(f"Error generating response: `GENRESPONSE-EFILL-{e}`")

    await bot.process_commands(message)


bot.run(TOKEN)
