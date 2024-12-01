import asyncio
import logging
import aio_pika
from aio_pika import Message
import grpc, json
import workerChar_pb2, workerChar_pb2_grpc
# import workerInit_pb2,workerInit_pb2_grpc
# import workerRoll_pb2,workerRoll_pb2_grpc
# import workerLookup_pb2,workerLookup_pb2_grpc
from concurrent import futures
import uuid
from typing import MutableMapping
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)
import os 
import sys
import dndio_pb2, dndio_pb2_grpc
import random # remove later?

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []

RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or '5672'

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig( 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)

class rmq_client():
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    def __init__(self,url,wrkr):
        self.url = url
        self.wrkr = wrkr
        self.futures: MutableMapping[str,asyncio.Future] = {}
    async def connect(self):
        logger.info("  [x] Establshing client connection to rmq db channel")
        self.connection = await aio_pika.connect(self.url)
        self.channel = await self.connection.channel()
        logger.info("  [x] establishing callback queue")
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response,no_ack=True)
        logger.info("  [x] client connection with callback queue established!")
        return self
    async def on_response(self, msg: AbstractIncomingMessage):
        if msg.correlation_id is None:
            logger.info(" [!] Received bad inbound response: {}".format(msg))
            return
        logger.info("  [!!!] futures: {}".format(self.futures))
        future: asyncio.Future = self.futures.pop(msg.correlation_id)
        logger.info("  [!!!] futures: {}".format(self.futures))
        future.set_result(msg.body)
        
    async def call(self,msg,correlation_id):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        logger.info("  [!!!] futures: {}".format(self.futures))
        await self.channel.default_exchange.publish(
            Message(
                msg,
                content_type='text/plain',
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key=self.wrkr
        )
        return await future

# class grpc_char_worker(workerChar_pb2_grpc.sendmsgServicer):
#     def __init__(self,rt_key,url):
#         self.rt_key = rt_key
#         self.url = url
#         self.rmq_cli = rmq_client(url,'grpc.workerchar')
#     async def sendmsg(
#         self,
#         request: workerChar_pb2.msg,
#         context: grpc.aio.ServicerContext,
#     ) -> workerChar_pb2.msgreply:
#         logger.info(" [x] grpc server - received new request: {}".format(request))
#         # self.rmq_cli = await self.rmq_cli.connect()
#         logger.info(" [x] grpc server - pushing request to rabbit mq")
#         corr_id = str(uuid.uuid4())
#         resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
#         logger.info(" [x] grpc server - received response from rabbit mq: {}".format(resp))
#         data = workerChar_pb2.msgreply()
#         data.ParseFromString(resp)
#         logger.info(" [x] Request complete - issuing reply to requestor...")
#         return data

class grpc_char_worker(dndio_pb2_grpc.charSvcServicer):
    def __init__(self,rt_key,url):
        self.rt_key = rt_key
        self.url = url
        self.rmq_cli = rmq_client(url,'grpc.workerchar')
    async def char(self,
                   request:dndio_pb2.dndiomsg,
                   context:grpc.aio.ServicerContext
    ) -> dndio_pb2.dndioreply:
        logger.info(" [x] grpc char server - received new request: {}".format(request))
        logger.info(" [x] grpc char server - pushing request to rabbit mq")
        corr_id = str(uuid.uuid4())
        # resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
        logger.info(" [x] grpc char server - received response from rabbit mq")
        logger.info(" [x] grpc char server - processing reply")
        data = dndio_pb2.dndioreply(
            orig_cmd=request.cmd,
            status=True,
            dc_channel = request.dc_channel,
            dc_user=request.user,
            addtl_data = 'Test successful',
            err_msg=None
        )
        char_reply = dndio_pb2.charreply(
            common = data
        )
        logger.info(" [x] grpc char server - request complete - issuing reply to requestor...")
        return char_reply

class grpc_lookup_worker(dndio_pb2_grpc.lookupSvcServicer):
    def __init__(self,rt_key,url):
        self.rt_key = rt_key
        self.url = url
        self.rmq_cli = rmq_client(url,'grpc.workerlookup')
    async def lookup(
        self,
        request: dndio_pb2.dndiomsg,
        context: grpc.aio.ServicerContext,
    ) -> dndio_pb2.dndioreply:
        logger.info(" [x] grpc lookup server - received new request: {}".format(request))
        # self.rmq_cli = await self.rmq_cli.connect()
        logger.info(" [x] grpc lookup server - pushing request to rabbit mq")
        corr_id = str(uuid.uuid4())
        # resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
        data = dndio_pb2.dndioreply(
            orig_cmd=request.cmd,
            status=True,
            dc_channel = request.dc_channel,
            dc_user=request.user,
            addtl_data = 'Test successful',
            err_msg=None
        )
        vals1 = dndio_pb2.lookupvalues(
            values = ['z','y','x']
        )
        vals2 = dndio_pb2.lookupvalues(
            values= ['w','v','u']
        )
        vals3 = dndio_pb2.lookupvalues(
            values= ['1','2','3']
        )
        lookup_reply = dndio_pb2.lookupreply(
            common = data,
            columns = ['a','b','c'],
            dtypes = [dndio_pb2.dtype.STR,dndio_pb2.dtype.STR,dndio_pb2.dtype.INT],
            values = [vals1,vals2,vals3]
        )
        logger.info(" [x] grpc lookup server - received response from rabbit mq")

        logger.info(" [x] grpc lookup server - request complete - issuing reply to requestor...")

        return lookup_reply

class grpc_roll_worker(dndio_pb2_grpc.rollSvcServicer):
    def __init__(self,rt_key,url):
        self.rt_key = rt_key
        self.url = url
        self.rmq_cli = rmq_client(url,'grpc.workerroll')
    async def roll(
        self,
        request: dndio_pb2.dndiomsg,
        context: grpc.aio.ServicerContext,
    ) -> dndio_pb2.rollreply:
        logger.info(" [x] grpc roll server - received new request: {}".format(request))
        # self.rmq_cli = await self.rmq_cli.connect()
        logger.info(" [x] grpc roll server - pushing request to rabbit mq")
        # corr_id = str(uuid.uuid4())
        # resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
        logger.info(" [x] grpc roll server - received response from rabbit mq: {}")#.format(resp))
        data = dndio_pb2.dndioreply(
            orig_cmd=request.cmd,
            status=True,
            dc_channel = request.dc_channel,
            dc_user=request.user,
            addtl_data = 'Test successful',
            err_msg=None
        )
        r1 = [random.randint(1,20) for i in range(2)]
        mr1 = [r+1 for r in r1]
        r2 = [random.randint(1,8) for i in range(3)]
        mr2 = [r+1 for r in r2]
        roll1 = dndio_pb2.roll(
            roll_type='initiative',
            die_rolls=r1,
            modifiers=[2,-1],
            modified_rolls=mr1,
            total=max(mr1)
        )
        roll2 = dndio_pb2.roll(
            roll_type='attack damage',
            die_rolls=r1,
            modifiers=[2,-1],
            modified_rolls=mr2,
            total=max(mr2)
        )
        roll_reply  = dndio_pb2.rollreply(
            common=data,
            dierolls=[roll1,roll2]
        )
        # data.ParseFromString(resp)
        logger.info(" [x] grpc roll server - request complete - issuing reply to requestor...")
        return roll_reply

class grpc_init_worker(dndio_pb2_grpc.initSvcServicer):
    def __init__(self,rt_key,url):
        self.rt_key = rt_key
        self.url = url
        self.rmq_cli = rmq_client(url,'grpc.workerinit')
    async def init(
        self,
        request: dndio_pb2.dndiomsg,
        context: grpc.aio.ServicerContext,
    ) -> dndio_pb2.initreply:
        logger.info(" [x] grpc init server - received new request: {}".format(request))
        # self.rmq_cli = await self.rmq_cli.connect()
        logger.info(" [x] grpc init server - pushing request to rabbit mq")
        corr_id = str(uuid.uuid4())
        # resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
        logger.info(" [x] grpc init server - received response from rabbit mq: {}")#.format(resp))
        # data = workerInit_pb2.msgreply()
        # data.ParseFromString(resp)
        logger.info(" [x] grpc init server - request complete - issuing reply to requestor...")
        data = dndio_pb2.dndioreply(
            orig_cmd=request.cmd,
            status=True,
            dc_channel = request.dc_channel,
            dc_user=request.user,
            addtl_data = 'Test successful',
            err_msg=None
        )
        init_reply = dndio_pb2.initreply(
            common = data
        )
        return init_reply

async def serve() -> None:
    server = grpc.aio.server()
    # gr = grpc_char_worker('grpc.workerchar','amqp://guest:guest@{}:{}'.format(
    #     RMQ_HOST,RMQ_PORT
    # ))
    # gr.rmq_cli = await gr.rmq_cli.connect()
    chr_wrkr = grpc_char_worker('grpc.workerchar','amqp://guest:guest@{}:{}'.format(
        RMQ_HOST,RMQ_PORT
    ))
    lkp_wrkr = grpc_lookup_worker('grpc.workerlookup','amqp://guest:guest@{}:{}'.format(
        RMQ_HOST,RMQ_PORT
    ))
    roll_wrkr = grpc_roll_worker('grpc.workerroll','amqp://guest:guest@{}:{}'.format(
        RMQ_HOST,RMQ_PORT
    ))
    init_wrkr = grpc_init_worker('grpc.workerinit','amqp://guest:guest@{}:{}'.format(
        RMQ_HOST,RMQ_PORT
    ))
    chr_wrkr.rmq_cli = await chr_wrkr.rmq_cli.connect()
    lkp_wrkr.rmq_cli = await lkp_wrkr.rmq_cli.connect()
    roll_wrkr.rmq_cli = await roll_wrkr.rmq_cli.connect()
    init_wrkr.rmq_cli = await init_wrkr.rmq_cli.connect()
    # workerChar_pb2_grpc.add_sendmsgServicer_to_server(chr_wrkr,server) #.add_GreeterServicer_to_server(Greeter(), server)
    dndio_pb2_grpc.add_charSvcServicer_to_server(chr_wrkr,server)
    dndio_pb2_grpc.add_lookupSvcServicer_to_server(lkp_wrkr,server)
    dndio_pb2_grpc.add_rollSvcServicer_to_server(roll_wrkr,server)
    dndio_pb2_grpc.add_initSvcServicer_to_server(init_wrkr,server)
    # workerRoll_pb2_grpc.add_sendmsgServicer_to_server(roll_wrkr,server)
    # workerInit_pb2_grpc.add_sendmsgServicer_to_server(init_wrkr,server)
    listen_addr = "localhost:5000"
    server.add_insecure_port(listen_addr)
    logger.info("Starting server on %s", listen_addr)
    await server.start()
    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()