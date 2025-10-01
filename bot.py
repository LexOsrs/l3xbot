


import discord
from discord.ext import commands
import config
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load cogs from cogs directory
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    logging.info("Synced application commands to Discord.")
    logging.info(f"Logged in as {bot.user}")
    # Log all registered commands
    for cmd in sorted(bot.tree.get_commands(), key=lambda c: c.name):
        logging.info(f"Available command: /{cmd.name} from {cmd.module}")


if __name__ == "__main__":
    asyncio.run(load_cogs())

    token = config.TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set.")

    bot.run(token)
