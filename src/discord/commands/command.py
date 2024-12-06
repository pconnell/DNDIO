from discord.ext.commands import Cog, Context, command
import random as rd
from argparse import ArgumentError

from src.aio.dndio_parser import parse_str
from src.aio.parser_protobuf import ParserProto
from ..discord_bot import DNDIO

class Commands(Cog):
    
    async def __init__(self, client: DNDIO):
        self.client = client

    async def parse(self, ctx: Context):
        try:
            await args = parse_str(ctx.message.content[1:])
            to_send = ParserProto(args, ctx)
            response = to_send.request(self.client.relay)
        except Exception as e:
            raise e
        return response

    @command()
    async def ping(self, ctx: Context):
        await ctx.reply(rd.choice(["Oh really?", "Test!", "yeah", "...Yes?", "Can you please stop that? It's getting very annoying.", "Pong!", ":face_with_raised_eyebrow:", "pong :index_pointing_at_the_viewer:"]), mention_author=False)

    @command()
    async def init(self, ctx: Context):
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

    @command()
    async def lookup(self, ctx: Context):
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

    @command()
    async def char(self, ctx: Context):
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

    @command()
    async def roll(self, ctx: Context):
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

async def setup(client):
    await client.add_cog(Commands(client))