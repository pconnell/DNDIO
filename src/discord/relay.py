import json
import grpc

import os; print(os.getcwd())

import dndio_pb2_grpc, dndio_pb2

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
        self.options = (
            ('grpc.ssl_target_name_override', self.cert_cn,),
            ('grpc.keepalive_time_ms',5000),
            ('grpc_keepalive_timeout_ms',10000),
        )

    async def connect(self): 
        self.channel = grpc.aio.secure_channel(
            self.target, 
            self.credentials, 
            self.options
        )
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
        return self

    def get_stub(self,channel,cmd):
        if cmd=='char':
            return dndio_pb2_grpc.charSvcStub(channel).char
        if cmd == 'lookup':
            return dndio_pb2_grpc.lookupSvcStub(channel).lookup
        if cmd == 'roll':
            return dndio_pb2_grpc.rollSvcStub(channel).roll
        if cmd == 'init':
            return dndio_pb2_grpc.initSvcStub(channel).init
        return None
        
    async def call(self,args: dict):
        await self.channel.channel_ready()
        #cmd - init/roll/lookup/char
        #subcmd - roll (damage|initiative|spell), char (add|remove|set|etc), ...
        #svr - name of the discord server
        #usr - the user sending up the command
        #args - the namespace arguments for the commands
        # print("call")
        stub = self.stubs.get(args.get("command"),None)
            
        # print(stub)
        if stub:
            # print(args)
            to_send = dndio_pb2.dndiomsg(
                cmd=args["command"],
                subcmd=args.get("subcommand", None),
                args=json.dumps(args),
                dc_channel=args["server"],
                user=args["user"]
            )
            # print(stub)
            reply = await stub['func'](to_send,timeout=10)
            # print(reply)
            return reply #may need handlers here to process the reply depending on type.
            #otherwise - we can return it as a string.
        else: 
            #not sure what/how to handle here...
            #basically means we got fed a b.s. set of params to call the function.
            raise Exception
