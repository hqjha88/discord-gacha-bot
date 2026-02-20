from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from datetime import datetime

# =========================
# WEB SERVER (FOR RENDER FREE)
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# =========================
# CONFIG
# =========================

GUILD_ID = 919604864185688165
GACHA_CHANNEL_ID = 1474397016082747422
GACHA_MESSAGE_ID = None  # ครั้งแรกให้เป็น None ก่อน

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# =========================
# LOAD / SAVE DATA
# =========================

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def update_nickname(member):
    user_id = str(member.id)
    points = data.get(user_id, 0)
    new_name = f"{member.name};{points}"
    try:
        await member.edit(nick=new_name)
    except:
        pass

# =========================
# GACHA SYSTEM
# =========================

rewards = [
    ("free 2 single pic", 5),
    ("free 1 single pic", 5),
    ("free 1 couple pic", 5),
    ("discount 5%", 5),
    ("add point +100", 30),
    ("add point +200", 20),
    ("add point +300", 20),
    ("add point +400", 5),
    ("add point +500", 5),
]

def roll_reward():
    total = sum(weight for _, weight in rewards)
    r = random.uniform(0, total)
    upto = 0
    for reward, weight in rewards:
        if upto + weight >= r:
            return reward
        upto += weight

# =========================
# PERSISTENT GACHA BUTTON
# =========================

class GachaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎲 Roll (300 points)",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_gacha_button"
    )
    async def roll_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user
        user_id = str(user.id)

        if data.get(user_id, 0) < 300:
            await interaction.response.send_message("❌ Not enough points", ephemeral=True)
            return

        data[user_id] -= 300
        reward = roll_reward()

        if "add point" in reward:
            amount = int(reward.split("+")[1])
            data[user_id] += amount

        save_data()
        await update_nickname(user)

        embed = discord.Embed(
            title="˚.🎀༘⋆ Gacha Result",
            description=f"🎉 Your reward: **{reward}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="💎 Your Points",
            value=f"{data[user_id]} points",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # DM ผู้ใช้
        try:
            await user.send(embed=embed)
        except:
            pass

        # DM เจ้าของเซิร์ฟ
        try:
            owner = interaction.guild.owner
            log_embed = discord.Embed(
                title="📢 Gacha Log",
                color=discord.Color.gold()
            )
            log_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
            log_embed.add_field(name="Reward", value=reward, inline=False)
            log_embed.add_field(
                name="Time",
                value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                inline=False
            )
            await owner.send(embed=log_embed)
        except:
            pass

# =========================
# CREATE GACHA MESSAGE
# =========================

async def create_gacha_message():
    channel = bot.get_channel(GACHA_CHANNEL_ID)

    embed = discord.Embed(
        title="🎰 Gacha Machine",
        description="Press the button to roll (300 points)",
        color=discord.Color.blue()
    )

    msg = await channel.send(embed=embed, view=GachaView())
    print("GACHA MESSAGE ID:", msg.id)

# =========================
# SLASH ADD POINTS (OWNER ONLY)
# =========================

@bot.tree.command(
    name="addpoints",
    description="Add points to a member",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(member="Member", amount="Amount of points")
async def addpoints_slash(interaction: discord.Interaction, member: discord.Member, amount: int):

    await interaction.response.send_message("⏳ Processing...", ephemeral=True)

    if interaction.user != interaction.guild.owner:
        await interaction.edit_original_response(content="❌ Owner only")
        return

    user_id = str(member.id)
    data[user_id] = data.get(user_id, 0) + amount
    save_data()

    await update_nickname(member)

    embed = discord.Embed(
        title="✨ Add Points Success",
        description=f"Added **{amount}** points to {member.mention}",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Current Points",
        value=f"{data[user_id]}",
        inline=False
    )

    await interaction.edit_original_response(content=None, embed=embed)

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():

    bot.add_view(GachaView())

    channel = bot.get_channel(GACHA_CHANNEL_ID)

    try:
        if GACHA_MESSAGE_ID:
            await channel.fetch_message(GACHA_MESSAGE_ID)
        else:
            await create_gacha_message()
    except:
        await create_gacha_message()

    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot is online as {bot.user}")

# =========================
# RUN BOT
# =========================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("ERROR: TOKEN not found")
else:
    keep_alive()
    bot.run(TOKEN)
