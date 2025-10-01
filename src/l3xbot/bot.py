import discord
from discord.ext import commands
import config
import asyncio
import logging
from cogs.general import General
from cogs.invo import Invo
from cogs.rank import Rank

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Add cogs
async def load_cogs():
    await bot.add_cog(General(bot))
    await bot.add_cog(Invo(bot))
    await bot.add_cog(Rank(bot))

@bot.event
async def on_ready():
    await bot.tree.sync()
    logging.info("Synced application commands to Discord.")
    logging.info(f"Logged in as {bot.user}")
    # Log all registered commands
    for cmd in sorted(bot.tree.get_commands(), key=lambda c: c.name):
        logging.info(f"Available command: /{cmd.name} from {cmd.module}")

def main():
    asyncio.run(load_cogs())

    token = config.TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set.")

    bot.run(token)

if __name__ == "__main__":
    main()