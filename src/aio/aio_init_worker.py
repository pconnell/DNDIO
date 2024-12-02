##################################################################
import aio_pika,os,json,uuid,logging,sys
from concurrent import futures
import uuid
from typing import MutableMapping
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)
from aio_pika import Message
import asyncio
# import workerInit_pb2, workerInit_pb2_grpc
import dndio_pb2, dndio_pb2_grpc
##################################################################

##################################################################
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
##################################################################

##################################################################
class rmq_client():
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    def __init__(self,url):
        self.url = url
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
                msg.encode('utf-8'),
                content_type='text/plain',
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key='worker.db'
        )
        return await future
##################################################################
QUERIES = {
    'init_campaign':""" 
INSERT INTO campaign (id,owner)
VALUES ('{}','{}');
""",
    'init_users':""" 
INSERT INTO users ({},{},{}) VALUES ({},{},{});
""",
    'create_chars':""" 
INSERT INTO characters () VALUES ();
""",
    '':""" 
"""
}
##################################################################
class rmq_server():
    def __init__(self,url,qname):
        self.connection = None
        self.channel = None 
        self.exchange = None
        self.queue = None
        self.qname = qname
        self.url = url
        self.rmq_client = rmq_client(url)

    async def connect(self):
        logger.info(" [x] Initializing RabbitMQ Async Connection")
        self.connection = await aio_pika.connect(
            self.url
        )
        logger.info(" [x] Connecting to RabbitMQ channel")
        self.channel = await self.connection.channel()
        self.exchange=self.channel.default_exchange
        logger.info(" [x] Establishing request queue: {}".format(self.qname))
        self.queue = await self.channel.declare_queue(self.qname)
        logger.info(" [x] Char Worker Listening for RPC Requests")


    async def run(self):
        await self.connect()
        self.rmq_client = await self.rmq_client.connect()
        async with self.queue.iterator() as qiter:
            msg: AbstractIncomingMessage
            async for msg in qiter:
                try:
                    assert msg.reply_to is not None
                    # do processing here...
                    logger.info("  [x] Received new RPC request: {}".format(msg))
                    
                    inbound_msg = dndio_pb2.dndiomsg() #workerInit_pb2.msg()
                    inbound_msg.ParseFromString(msg.body)
                    args = json.loads(inbound_msg.args)
                    logger.info("  [x] Parsed RPC to GRPC, converting to query")
                    resps = []
                    if args['owner'] is not None:
                        query = """INSERT INTO campaign (id,owner) VALUES ('{}','{}') IF NOT EXISTS""".format(
                            inbound_msg.dc_channel,args['owner']
                        )
                        corr_id = str(uuid.uuid4())
                        logger.info(f"  [x] Query generated {query}, sending to db worker...")
                        resp = await self.rmq_client.call(query,corr_id)
                        resps.append(resp)
                    for user in args['users']:
                        # make sure that the campaign exists
                        query = "SELECT * FROM campaign WHERE id='{}'".format(
                            inbound_msg.dc_channel
                        )
                        corr_id = str(uuid.uuid4())
                        logger.info(f"  [x] Verifying campaign exists...")
                        resp = await self.rmq_client.call(query,corr_id)
                        resp = json.loads(resp)['rows']
                        if len(resp) == 0:
                            #campaign doesn't exist
                            c = dndio_pb2.dndioreply(
                                orig_cmd='init',
                                dc_channel=inbound_msg.dc_channel,
                                dc_user=inbound_msg.user,
                                status=False,
                                err_msg='Campaign {} does not exist, create a campaign with an owner first'
                            )
                            ret = dndio_pb2.initreply(
                                common=c
                            )
                            await self.exchange.publish(
                                Message(
                                    body=ret.SerializeToString(),
                                    correlation_id=msg.correlation_id
                                ),
                                routing_key=msg.reply_to
                            )
                        else:
                            query = """INSERT INTO char_table (campaign_id,char_id) VALUES ('{}','{}') IF NOT EXISTS""".format(
                                inbound_msg.dc_channel,user
                            )
                            corr_id = str(uuid.uuid4())
                            logger.info(f"   [x] Query generated {query}, sending to db worker...")
                            resp = await self.rmq_client.call(query,corr_id)
                            resps.append(resp)
                    #do error checking on responses - handle later
                    c = dndio_pb2.dndioreply(
                        orig_cmd='init',
                        dc_channel=inbound_msg.dc_channel,
                        dc_user=inbound_msg.user,
                        status=True,
                        addtl_data='',
                        err_msg=''
                    )
                    ret = dndio_pb2.initreply(
                        common=c
                    )

                except:
                    c = dndio_pb2.dndioreply(
                        orig_cmd='',
                        dc_channel=inbound_msg.dc_channel,
                        dc_user=inbound_msg.user,
                        err_msg='Unknown Error'
                    )
                    ret = dndio_pb2.initreply(common=c)
                finally:
                    await self.exchange.publish(
                        Message(
                            body=ret.SerializeToString(),
                            correlation_id=msg.correlation_id
                        ),
                        routing_key=msg.reply_to
                    )



if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerinit')
    asyncio.run(worker.run())