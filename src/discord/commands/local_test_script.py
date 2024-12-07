from commands.dndio_parser import *
import dndio_pb2, dndio_pb2_grpc
import json
import grpc
import asyncio
from relay import grpc_relay

async def main():
    relay = grpc_relay('73.95.249.208','44443','./dndio-tls.crt')
    while True:
        x = input("Enter a command: ")
        args = parser.parse_args(shlex.split(x))
        # print(vars(args))
        args = vars(args)
        print(args)
        response = await relay.call(
            svr='abcdef', 
            usr= 'asticky#2319', #'chorky#8402',
            cmd=args['command'],
            subcmd=args['subcommand'],
            args=args
            #parser.parse_args(shlex.split(x))
        )
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
