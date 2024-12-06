from discord.ext.commands import Cog, Context, command
import random as rd
from argparse import ArgumentError

from src.aio import dndio_parser
from ..discord_bot import DNDIO

class Commands(Cog):
    def __init__(self, client: DNDIO):
        self.client = client

    @command()
    async def ping(self, ctx: Context):
        await ctx.reply(rd.choice(["Oh really?", "Test!", "yeah", "...Yes?", "Can you please stop that? It's getting very annoying.", "Pong!", ":face_with_raised_eyebrow:", "pong :index_pointing_at_the_viewer:"]), mention_author=False)

    @command()
    async def init(self, ctx: Context):
        response = await self._parse_dndio_command(ctx.message)
        await ctx.reply(response, mention_author=False)

    @command()
    async def lookup(self, ctx: Context):
        response = await self._parse_dndio_command(ctx.message)
        await ctx.reply(response, mention_author=False)

    @command()
    async def char(self, ctx: Context):
        response = await self._parse_dndio_command(ctx.message)
        await ctx.reply(response, mention_author=False)

    @command()
    async def roll(self, ctx: Context):
        response = await self._parse_dndio_command(ctx.message)
        await ctx.reply(response, mention_author=False)
    
    async def _parse_dndio_command(self, message): #,ctx:Context): too if we want to parse cmd/subcmd here, otherwise we need to feed them over.
        try:
            result = dndio_parser.parse_str(message.content[1:])
            if type(result) == ArgumentError:
                print(result)
            #this'll need some tweaks... basically 
            #we want to use this to make sure we're sending the right
            #params up to the grpc_relay instance
            # userid = ctx.author.id
            # chan = ctx.message.guild.name #not sure if this is right - just need the DC server name.
            # svc_reply = await self.relay.call(
            #     '','',chan,userid,result
            # )
        except (Exception, SystemExit) as e:
            print(e)
            result = f"Error parsing command: {str(e)}"

        #do something here to clean/format/etc our response...from svc_reply
        return str(result)

async def setup(client):
    await client.add_cog(Commands(client))