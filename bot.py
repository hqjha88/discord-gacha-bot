import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from datetime import datetime

# =========================
# CONFIG
# =========================

GUILD_ID = 919604864185688165
ALLOWED_CHANNEL_ID = 1087434625569280150

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
# SLASH ROLL COMMAND
# =========================

@bot.tree.command(
    name="roll",
    description="Use 300 points to gacha",
    guild=discord.Object(id=GUILD_ID)
)
async def roll_slash(interaction: discord.Interaction):

    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ Wrong channel", ephemeral=True)
        return

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

    # เห็นเฉพาะผู้ใช้
    await interaction.response.send_message(embed=embed, ephemeral=True)

    # ================= DM ผู้ใช้ =================
    try:
        await user.send(embed=embed)
    except:
        pass

    # ================= แจ้งเจ้าของเซิร์ฟ =================
    try:
        owner = interaction.guild.owner

        log_embed = discord.Embed(
            title="📢 Gacha Log",
            color=discord.Color.gold()
        )

        log_embed.add_field(
            name="User",
            value=f"{user} ({user.id})",
            inline=False
        )

        log_embed.add_field(
            name="Reward",
            value=reward,
            inline=False
        )

        log_embed.add_field(
            name="Time",
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )

        await owner.send(embed=log_embed)
    except:
        pass


# =========================
# SLASH ADD POINTS (OWNER ONLY)
# =========================

@bot.tree.command(
    name="addpoints",
    description="Add points to a member",
)
@app_commands.describe(member="Member", amount="Amount of points")
async def addpoints_slash(interaction: discord.Interaction, member: discord.Member, amount: int):

    await interaction.response.send_message("⏳ Processing...", ephemeral=True)

    if interaction.user != interaction.guild.owner:
        await interaction.edit_original_response(content="❌ Owner only")
        return

    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.edit_original_response(content="❌ Wrong channel")
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
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

    print(f"Bot is online as {bot.user}")


# =========================
# RUN BOT (ENV TOKEN)
# =========================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("ERROR: TOKEN not found in environment variables")
else:
    bot.run(TOKEN)

