from parser_script import parser
import sys
import dndio_pb2,dndio_pb2_grpc
from argparse import Namespace
import json
import grpc


if __name__ == '__main__':
    if len(sys.argv) > 0:
        #sys.argv will change for the discord bot - this works for cli testing
        args = parser.parse_args()
        #build a basic message based upon the 
        # command line arguments
        # take the args and parse them to a dictionary and dump into a string

        to_send = dndio_pb2.dndiomsg(
            cmd = sys.argv[1],
            subcmd= sys.argv[2],
            args = json.dumps(vars(args)),
            dc_channel='abcdef',
            user = 'chorky#8402'
        )
        print(vars(args))
        print('*'*80) 
        print(to_send)
        print('*'*80)
        # connect to the grpc server - will change
        channel = grpc.insecure_channel('localhost:5000')
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