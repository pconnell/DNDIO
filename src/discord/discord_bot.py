import logging, base64, jsonpickle, io
import redis, json, hashlib

import requests, base64, json, os, glob, subprocess, jsonpickle

import discord
from discord.ext import commands

from cogwatch import watch

import google.protobuf

class DNDIO(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='~', intents=intents)

    @watch(path='src/discord/commands', preload=True)
    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author.bot:
            return
    
        await self.process_commands(message)