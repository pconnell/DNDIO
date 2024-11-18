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

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []

RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or 5672

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

class grpc_char_worker(workerChar_pb2_grpc.sendmsgServicer):
    def __init__(self,rt_key,url):
        self.rt_key = rt_key
        self.url = url
        self.rmq_cli = rmq_client(url,'grpc.workerchar')
    async def sendmsg(
        self,
        request: workerChar_pb2.msg,
        context: grpc.aio.ServicerContext,
    ) -> workerChar_pb2.msgreply:
        logger.info(" [x] grpc server - received new request: {}".format(request))
        # self.rmq_cli = await self.rmq_cli.connect()
        logger.info(" [x] grpc server - pushing request to rabbit mq")
        corr_id = str(uuid.uuid4())
        resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
        logger.info(" [x] grpc server - received response from rabbit mq: {}".format(resp))
        data = workerChar_pb2.msgreply()
        data.ParseFromString(resp)
        logger.info(" [x] Request complete - issuing reply to requestor...")
        return data


# class grpc_lookup_worker(workerLookup_pb2_grpc.sendmsgServicer):
#     def __init__(self,rt_key,url):
#         self.rt_key = rt_key
#         self.url = url
#         self.rmq_cli = rmq_client(url,'grpc.workerlookup')
#     async def sendmsg(
#         self,
#         request: workerLookup_pb2.msg,
#         context: grpc.aio.ServicerContext,
#     ) -> workerRoll_pb2.msgreply:
#         logger.info(" [x] grpc server - received new request: {}".format(request))
#         # self.rmq_cli = await self.rmq_cli.connect()
#         logger.info(" [x] grpc server - pushing request to rabbit mq")
#         corr_id = str(uuid.uuid4())
#         resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
#         logger.info(" [x] grpc server - received response from rabbit mq: {}".format(resp))
#         data = workerLookup_pb2.msgreply()
#         data.ParseFromString(resp)
#         logger.info(" [x] Request complete - issuing reply to requestor...")
#         return data

# class grpc_roll_worker(workerRoll_pb2_grpc.sendmsgServicer):
#     def __init__(self,rt_key,url):
#         self.rt_key = rt_key
#         self.url = url
#         self.rmq_cli = rmq_client(url,'grpc.workerroll')
#     async def sendmsg(
#         self,
#         request: workerRoll_pb2.msg,
#         context: grpc.aio.ServicerContext,
#     ) -> workerRoll_pb2.msgreply:
#         logger.info(" [x] grpc server - received new request: {}".format(request))
#         # self.rmq_cli = await self.rmq_cli.connect()
#         logger.info(" [x] grpc server - pushing request to rabbit mq")
#         corr_id = str(uuid.uuid4())
#         resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
#         logger.info(" [x] grpc server - received response from rabbit mq: {}".format(resp))
#         data = workerRoll_pb2.msgreply()
#         data.ParseFromString(resp)
#         logger.info(" [x] Request complete - issuing reply to requestor...")
#         return data

# class grpc_init_worker(workerInit_pb2_grpc.sendmsgServicer):
#     def __init__(self,rt_key,url):
#         self.rt_key = rt_key
#         self.url = url
#         self.rmq_cli = rmq_client(url,'grpc.workerinit')
#     async def sendmsg(
#         self,
#         request: workerInit_pb2.msg,
#         context: grpc.aio.ServicerContext,
#     ) -> workerInit_pb2.msgreply:
#         logger.info(" [x] grpc server - received new request: {}".format(request))
#         # self.rmq_cli = await self.rmq_cli.connect()
#         logger.info(" [x] grpc server - pushing request to rabbit mq")
#         corr_id = str(uuid.uuid4())
#         resp = await self.rmq_cli.call(request.SerializeToString(),corr_id)
#         logger.info(" [x] grpc server - received response from rabbit mq: {}".format(resp))
#         data = workerInit_pb2.msgreply()
#         data.ParseFromString(resp)
#         logger.info(" [x] Request complete - issuing reply to requestor...")
#         return data

async def serve() -> None:
    server = grpc.aio.server()
    # gr = grpc_char_worker('grpc.workerchar','amqp://guest:guest@{}:{}'.format(
    #     RMQ_HOST,RMQ_PORT
    # ))
    # gr.rmq_cli = await gr.rmq_cli.connect()
    chr_wrkr = grpc_char_worker('grpc.workerchar','amqp://guest:guest@{}:{}'.format(
        RMQ_HOST,RMQ_PORT
    ))
    # lkp_wrkr = grpc_lookup_worker('grpc.workerlookup','amqp://guest:guest@{}:{}'.format(
    #     RMQ_HOST,RMQ_PORT
    # ))
    # roll_wrkr = grpc_char_worker('grpc.workerroll','amqp://guest:guest@{}:{}'.format(
    #     RMQ_HOST,RMQ_PORT
    # ))
    # init_wrkr = grpc_char_worker('grpc.workerinit','amqp://guest:guest@{}:{}'.format(
    #     RMQ_HOST,RMQ_PORT
    # ))
    chr_wrkr.rmq_cli = await chr_wrkr.rmq_cli.connect()
    # lkp_wrkr.rmq_cli = await lkp_wrkr.rmq_cli.connect()
    # roll_wrkr.rmq_cli = await roll_wrkr.rmq_cli.connect()
    # init_wrkr.rmq_cli - await init_wrkr.rmq_cli.connect()
    workerChar_pb2_grpc.add_sendmsgServicer_to_server(chr_wrkr,server) #.add_GreeterServicer_to_server(Greeter(), server)
    # workerLookup_pb2_grpc.add_sendmsgServicer_to_server(lkp_wrkr,server)
    # workerRoll_pb2_grpc.add_sendmsgServicer_to_server(roll_wrkr,server)
    # workerInit_pb2_grpc.add_sendmsgServicer_to_server(init_wrkr,server)
    listen_addr = "[::]:5000"
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