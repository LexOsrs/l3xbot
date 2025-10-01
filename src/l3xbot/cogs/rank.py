
from discord.ext import commands
import discord

class Rank(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@discord.app_commands.command(name="showrank", description="Show current rank")
	async def show_rank(self, interaction: discord.Interaction):
		await interaction.response.send_message("Your current rank is: **Gold** :star:")
