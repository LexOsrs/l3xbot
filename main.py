import discord
from discord import app_commands
from invocations import pick_best_invocations
from image import generate_image
import os

class MyClient(discord.Client):
    async def on_ready(self):
        await tree.sync()
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="invo",
    description="Show ToA Invocation",
)
async def show_invo_image(interaction, level: int):
    desired_level = int(5 * (level / 5))
    file = f"images/invo_{desired_level}.png"

    if not os.path.exists(file):
        # Not been requested before, generate
        invocations = pick_best_invocations(desired_level)
        generate_image(file, invocations)

    await interaction.response.send_message(f"Raid level {desired_level}", file=discord.File(file))


client.run(token=os.getenv("BOT_TOKEN"))
