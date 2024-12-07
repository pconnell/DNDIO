from discord.ext.commands import Cog, Context, command
import random as rd
from argparse import ArgumentError

# from src.aio.dndio_parser import parse_str
from commands.dndio_parser import parse_str
# from src.aio.parser_protobuf import ParserProto
from discord_bot import DNDIO
from relay import grpc_relay
import json

class Commands(Cog):
    
    def __init__(self, client: DNDIO):
        self.client = client
        #give this instance an instance of the relay - may want to parameterize this in the future.
        self.relay = client.relay

    async def parse(self, ctx: Context):
        try:
            print(f"Parsing command request {ctx.message.content}")
            args = parse_str(ctx.message.content[1:])
            print(f"Parsed string as {args}")
        
            args = vars(args)

            # TODO (later down the line): if command is init and args has username, get user id
            # if args["command"] == "init":
            #     print(args)
            #     return NotImplemented
            #     if args["users"] or args["owner"] is not None:
            #         print(args["users"], args["owner"])
                    
            #         pass

            args["server"] = str(ctx.guild.id)
            args["user"] = str(ctx.author.name)
            # to_send = ParserProto(args,ctx)
            # response = to_send.request(self.client.relay)
            #use our own relay instance to call and respond
            print(f"Sending {args['command']} request from user {ctx.author.name}")
            print(self.relay.target)
            response = await self.relay.call(
                args
            )
        except Exception as e:
            response = e
        return response

    @command()
    async def ping(self, ctx: Context):
        print(f"Received ping message from user {ctx.author.name}")
        await ctx.reply(rd.choice(["Oh really?", "Test!", "yeah", "...Yes?", "Can you please stop that? It's getting very annoying.", "Pong!", ":face_with_raised_eyebrow:", "pong :index_pointing_at_the_viewer:"]), mention_author=False)

    @command()
    async def init(self, ctx: Context):
        print(f"Received init request from user {ctx.author.name}")
        response = await self.parse(ctx)
        if response:
            await ctx.reply(response, mention_author=False)

    @command()
    async def lookup(self, ctx: Context):
        print(f"Received lookup request from user {ctx.author.name}")
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

    @command()
    async def char(self, ctx: Context):
        print(f"Received char request from user {ctx.author.name}")
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

    @command()
    async def roll(self, ctx: Context):
        print(f"Received roll request from user {ctx.author.name}")
        response = await self.parse(ctx)
        await ctx.reply(response, mention_author=False)

async def setup(client):
    await client.add_cog(Commands(client))