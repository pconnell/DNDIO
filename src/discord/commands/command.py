from discord.ext.commands import Cog, Context, command
import random as rd
from argparse import ArgumentError

import grpc,json
from src .aio import dndio_parser, parser_protobuf,dndio_pb2_grpc,dndio_pb2
from ..discord_bot import DNDIO


class grpc_relay():
    def __init__(self,ip:str,port:str,tls_crt:str):
        #ip: target IP addr of the service
        #port: port number upon which the service is running.
        #tls crt: filepath for the TLS certificate.
        #if needed...the bytes can be uploaded raw into this file. 
        #idk how the DC bots work.
        self.target = "{}:{}".format(
            ip,port
        )
        self.crt = tls_crt
        with open(self.crt,'rb') as f:
            self.cert_bytes = f.read()

        #this overrides the cert common name because it's not signed by a publically trusted entity (self-signed)
        self.credentials = grpc.ssl_channel_credentials(self.cert_bytes)
        self.cert_cn = 'rest.default.svc.cluster.local'
        self.options = (('grpc.ssl_target_name_override', self.cert_cn,),)
        #may need to be an aio channel...
        self.channel = grpc.secure_channel(self.credentials,self.options)
        self.ch_stub = dndio_pb2_grpc.charSvcStub(self.channel)
        self.init_stub = dndio_pb2_grpc.initSvcStub(self.channel)
        self.lookup_stub = dndio_pb2_grpc.lookupSvcStub(self.channel)
        self.roll_stub = dndio_pb2_grpc.rollSvcStub(self.channel)
        self.stubs = {
            'char':{'stub':self.ch_stub,'func':self.ch_stub.char},
            'init':{'stub':self.init_stub,'func':self.init_stub.init},
            'lookup':{'stub':self.lookup_stub,'func':self.lookup_stub.lookup},
            'roll':{'stub':self.roll_stub,'func':self.roll_stub.roll}
        }
    async def call(self,cmd,subcmd,svr,usr,args):
        #cmd - init/roll/lookup/char
        #subcmd - roll (damage|initiative|spell), char (add|remove|set|etc), ...
        #svr - name of the discord server
        #usr - the user sending up the command
        #args - the namespace arguments for the commands
        stub = self.stubs.get(cmd,None)
        if stub:
            to_send = dndio_pb2.dndiomsg(
                cmd=cmd,
                subcmd=subcmd,
                args=json.dumps(vars(args)),
                dc_channel=svr,
                user=usr
            )
            reply = await stub['func'](to_send)
            return reply #may need handlers here to process the reply depending on type.
            #otherwise - we can return it as a string.
        else: 
            #not sure what/how to handle here...
            #basically means we got fed a b.s. set of params to call the function.
            return ""

class Commands(Cog):
    def __init__(self, client: DNDIO): #svr_ip_addr:str, svr_port:str, tls_crt: str): for future implementation?
        self.client = client
        #currently hard-coded to be @ home server...this can be updated.
        self.relay = grpc_relay('73.95.249.208','44443','../aio/dndio-tls.crt')

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