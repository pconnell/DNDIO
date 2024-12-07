import json
import grpc

import discord
from discord.ext import commands

from cogwatch import watch

import dndio_pb2_grpc,dndio_pb2
from relay import grpc_relay

class DNDIO(commands.Bot):
    def __init__(self, relay: grpc_relay):
        intents = discord.Intents.default()
        intents.message_content = True
        self.relay = relay

        super().__init__(command_prefix='/', intents=intents)

    @watch(path='commands/command.py', preload=True)
    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author.bot:
            return
    
        await self.process_commands(message)

