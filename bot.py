import discord
from discord.ext import commands
import asyncio
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready and active on all servers.')

# --- Giveaway Command ---
class GiveawayView(discord.ui.View):
    def __init__(self, bot, prize, duration, channel):
        super().__init__(timeout=duration)
        self.bot = bot
        self.prize = prize
        self.channel = channel
        self.entries = []
        
    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.primary, emoji="🎉")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.entries:
            self.entries.append(interaction.user)
            await interaction.response.send_message(f"You have entered the giveaway for **{self.prize}**!", ephemeral=True)
        else:
            await interaction.response.send_message("You have already entered this giveaway.", ephemeral=True)

    async def on_timeout(self):
        if not self.entries:
            await self.channel.send("The giveaway has ended with no winner.")
            return
            
        winner = random.choice(self.entries)
        await self.channel.send(f"🎉 **GIVEAWAY ENDED** 🎉\n\nCongratulations, {winner.mention}! You won **{self.prize}**!")
        
@bot.command()
@commands.has_permissions(manage_guild=True)
async def giveaway(ctx, duration_minutes: int, *, prize: str):
    """Starts a giveaway for a specified duration and prize."""
    embed = discord.Embed(
        title="🎉 Giveaway! 🎉",
        description=f"**Prize:** {prize}\n**Duration:** {duration_minutes} minutes\n\nClick the button below to enter!",
        color=discord.Color.gold()
    )
    
    view = GiveawayView(bot, prize, duration_minutes * 60, ctx.channel)
    await ctx.send(embed=embed, view=view)


# --- Ticket Panel System ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Create a Ticket", style=discord.ButtonStyle.secondary, emoji="🎟️", custom_id="ticket_button")
    async def ticket_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        
        if not category:
            category = await guild.create_category("Tickets")

        ticket_channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)
        
        await interaction.response.send_message(f"A new ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
        close_button = discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
        async def close_ticket_callback(interaction: discord.Interaction):
            await ticket_channel.delete()
            
        close_button.callback = close_ticket_callback
        close_view = discord.ui.View()
        close_view.add_item(close_button)
        
        await ticket_channel.send(f"{interaction.user.mention}, A staff member will be with you shortly.", view=close_view)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def ticketpanel(ctx):
    """Sends the ticket panel with a button."""
    embed = discord.Embed(
        title="Support Tickets", 
        description="Click the button below to create a new support ticket.",
        color=discord.Color.blue()
    )
    view = TicketView()
    await ctx.send(embed=embed, view=view)


# --- Embed Builder Command ---
class EmbedModal(discord.ui.Modal, title="Create an Embed"):
    title = discord.ui.TextInput(label="Title", max_length=256, required=False)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, max_length=4000, required=False)
    color = discord.ui.TextInput(label="Color (Hex Code, e.g., #FF5733)", max_length=7, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed_color = int(self.color.value.replace("#", "0x"), 16) if self.color.value else discord.Embed.Empty
        except (ValueError, TypeError):
            embed_color = discord.Color.red()

        embed = discord.Embed(
            title=self.title.value or discord.Embed.Empty,
            description=self.description.value or discord.Embed.Empty,
            color=embed_color
        )
        await interaction.response.send_message(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def embed(ctx):
    """Creates an embed with a modal."""
    modal = EmbedModal()
    await ctx.interaction.response.send_modal(modal)


# --- Run the bot ---
# Get the token securely from the .env file
bot.run(os.getenv('TOKEN'))
