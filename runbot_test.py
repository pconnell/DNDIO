import asyncio, os
from discord.ext import commands
from dotenv import load_dotenv

from src.discord.discord_bot import DNDIO

async def main():
    load_dotenv("src/discord/.env")
    try:
        token = os.getenv("DISCORD_TOKEN")
    except:
        raise NameError("No Discord bot token could be read from .env.")    
    
    bot = DNDIO()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())