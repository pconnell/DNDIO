from commands.dndio_parser import *
import dndio_pb2, dndio_pb2_grpc
import json
import grpc
import asyncio
from relay2 import grpc_relay

async def main():

    relay = await grpc_relay('73.95.249.208','44443','./commands/dndio-tls.crt').connect()

    while True:
        x = input("Enter a command: ")
        args = parser.parse_args(shlex.split(x))
        args = vars(args)
        print('*'*80)
        print(args)
        print('*'*40)
        args['server'] = '1295825498231934987'
        args['user'] = 'chorky.'
        response = await relay.call(
            args
        )
        print(response)
        print('*'*80)

if __name__ == "__main__":
    asyncio.run(main())
