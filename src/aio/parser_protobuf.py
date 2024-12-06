from src .aio .parser import *
import sys
import os
print(os.getcwd())
from src .aio import dndio_pb2, dndio_pb2_grpc
from argparse import Namespace
import json
import grpc

if __name__ == '__main__':
    while True:
        x = input("Enter a command: ")
        #sys.argv will change for the discord bot - this works for cli testing
        dat = x.split(' ')
        args = parser.parse_args(shlex.split(x))
        #build a basic message based upon the 
        # command line arguments
        # take the args and parse them to a dictionary and dump into a string
        if dat[0]!='init':
            to_send = dndio_pb2.dndiomsg(
                cmd = dat[0],
                subcmd= dat[1],
                args = json.dumps(vars(args)),
                dc_channel='abcdef',
                user = 'chorky#8402'
            )
        else:
            dc = input("please enter the server name: ")
            print(vars(args))
            to_send = dndio_pb2.dndiomsg(
                cmd = 'init',
                subcmd= "",
                args = json.dumps(vars(args)),
                dc_channel=dc,
                user = 'chorky#8402'
            )
        print(vars(args))
        print('*'*80) 
        print(to_send)
        print('*'*80)
        # connect to the grpc server - will change
        # channel = grpc.insecure_channel('localhost:5000')
        with open('./dndio-tls.crt', 'rb') as f:
            cert_bytes = f.read()
        credentials = grpc.ssl_channel_credentials(cert_bytes)
        cert_cn = 'rest.default.svc.cluster.local'
        options = (('grpc.ssl_target_name_override', cert_cn,),)
        # channel = grpc.secure_channel('localhost:443', credentials, options)
        #channel = grpc.secure_channel('192.168.0.110:443',credentials,options)
        channel = grpc.secure_channel('73.95.249.208:44443',credentials,options)
        #build all stubs
        #use them in a dict to lookup which to use
        ch_stub = dndio_pb2_grpc.charSvcStub(channel)
        init_stub = dndio_pb2_grpc.initSvcStub(channel)
        lookup_stub = dndio_pb2_grpc.lookupSvcStub(channel)
        roll_stub = dndio_pb2_grpc.rollSvcStub(channel)
        stubs = {
            'char':{'stub':ch_stub,'func':ch_stub.char},
            'init':{'stub':init_stub,'func':init_stub.init},
            'lookup':{'stub':lookup_stub,'func':lookup_stub.lookup},
            'roll':{'stub':roll_stub,'func':roll_stub.roll}
        }
        cmds = {}
        print(to_send.cmd)
        #extract the function to use based off of sys arguments
        call = stubs[to_send.cmd]['func']
        #send off the request and get the reply
        reply = call(to_send)
        print('*'*80)
        print(reply)
        # print(reply.common)
        print('*'*80)