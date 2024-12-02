import logging, base64, jsonpickle, io
import redis, json, os, hashlib

import requests, base64, json, os, glob, subprocess, jsonpickle

import discord
import argparse

import google.protobuf

from . .aio import parser

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('~'):
        try:
            result = parser.parse_str(message.content[1:])
        except Exception as e:
            print(type(e))
            result = e
        except SystemExit as e:
            result = e
        
        await message.channel.send(result)

def run_bot(token=None):
    try:
        client.run(token)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    import sys
    token = sys.argv[1]
    run_bot(token)