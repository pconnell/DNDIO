import asyncio, os
from discord.ext import commands
from dotenv import load_dotenv

from src.discord.discord_bot import DNDIO, grpc_relay

async def main():
    load_dotenv("src/discord/.env")

    token = os.getenv("DISCORD_TOKEN")
    ip = os.getenv('PUBLIC_IP')
    port = os.getenv('PORT')
    tls = os.getenv('TLS_CERT')    
    
    relay = grpc_relay(ip, port, tls)

    bot = DNDIO(relay)
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())