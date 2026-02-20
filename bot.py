import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os

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

class RollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎰 Random (use 300 point)",
        style=discord.ButtonStyle.green,
        custom_id="persistent_roll_button"
    )
    async def roll_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user
        user_id = str(user.id)

        if data.get(user_id, 0) < 300:
            await interaction.response.send_message("❌ Not enough points", ephemeral=True)
            return

        await interaction.response.send_message(
            "⚠️ Use 300 points to gacha?",
            view=ConfirmView(),
            ephemeral=True
        )

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        user_id = str(user.id)

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

        await interaction.followup.send(embed=embed)

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
# PREFIX COMMAND
# =========================

@bot.command()
async def sendroll(ctx):
    await ctx.send(
        "Press the button below for a random reward 🎰",
        view=RollView()
    )

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally")
    except Exception as e:
        print("Sync error:", e)

    bot.add_view(RollView())
    print(f"Bot is online as {bot.user}")

# =========================
# RUN BOT (ENV TOKEN)
# =========================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("ERROR: TOKEN not found in environment variables")
else:
    bot.run(TOKEN)