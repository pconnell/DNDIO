from src.aio.dndio_parser import *
import sys
from src.aio import dndio_pb2, dndio_pb2_grpc
from argparse import Namespace
import json
import grpc
from src.discord.discord_bot import grpc_relay

class ParserProto:
    def __init__(self, args: Namespace, context):
        self.args = dndio_pb2.dndiomsg(
            cmd = args.command,
            subcmd= args.subcommand,
            args = json.dumps(vars(args)),
            dc_channel=context.channel,
            user = context.author
        )

    def request(self, relay):
        with open(relay.tls, 'rb') as f:
            cert_bytes = f.read()
        credentials = grpc.ssl_channel_credentials(cert_bytes)
        # Does this cert_cn parameter need to be changed/passed in elsewhere?
        cert_cn = 'rest.default.svc.cluster.local'
        options = (('grpc.ssl_target_name_override', cert_cn,),)
        channel = grpc.secure_channel(relay.ip,credentials,options)
        
        #build all stubs
        #use them in a dict to lookup which to use
        ch_stub = dndio_pb2_grpc.charSvcStub(channel)
        init_stub = dndio_pb2_grpc.initSvcStub(channel)
        lookup_stub = dndio_pb2_grpc.lookupSvcStub(channel)
        roll_stub = dndio_pb2_grpc.rollSvcStub(channel)
        
        # We could use reflection for this, but atm it's not used so I'm not gonna spend time on it
        stubs = {
            'char':{'stub':ch_stub,'func':ch_stub.char},
            'init':{'stub':init_stub,'func':init_stub.init},
            'lookup':{'stub':lookup_stub,'func':lookup_stub.lookup},
            'roll':{'stub':roll_stub,'func':roll_stub.roll}
        }
        cmds = {}

        reply = relay.call(self.args)


if __name__ == "__main__":
    while True:
        x = input("Enter a command: ")
        args = parser.parse_args(x)
        result = ParserProto(x)
        response = result.request()