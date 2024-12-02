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
import workerChar_pb2, workerChar_pb2_grpc

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
    'set_attr':"UPDATE characters SET {} WHERE char_id='{}' and campaign_id='{}';",
    'add_char':"UPDATE char_map SET {} = {} + {} WHERE char_id='{}' and campaign_id='{}';",
    'remove_char':"UPDATE char_map SET {} = {} - {} WHERE char_id='{}' and campaign_id='{}';",
    'get_char':"",
    'get_all':"",
    'get_char_weapon':"",
    'get_char_spells':"",
    'get_armor':"",
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

    #when can certain things not be set? and where should that be handled?

        # character stats between 1 and 20?

        # proficiency bonus - automatically handle?

        # a spell that's outside of the character's class

    async def add_char():
        pass

    async def spell_char():
        pass
    
    async def ability_char():
        pass

    async def skill_char():
        pass



    async def set_char(self,msg):
        campaign = msg.dc_channel,
        user = msg.user
        args = json.loads(msg.args)
        funcs = {
            'ability':self.ability_char,
            'skill':self.skill_char,
            'item':self.add_char,
            'spell':self.spell_char,
        }
        func = funcs[args['action']] #?
        resp = await func(args)
        
        pass

    async def get_char(self):
        pass

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
                    
                    inbound_msg = workerChar_pb2.msg()
                    inbound_msg.ParseFromString(msg.body)
                    logger.info("  [x] Parsed RPC to GRPC, converting to query")
                    ##### HERE'S WHERE WE'LL PARSE THE MESSAGE FROM THE CLIENT
                    ## AND USE THAT TO CRAFT DIFFERENT QUERIES
                    ## the parsed command gets fed to one of the above char get/set functions
                    ## and it will handle the query routing and response
                    ## each will return a response to this function, and this function
                    ## will send the final message.
                    query = "INSERT INTO worker (id,cmd,num) VALUES (uuid(),'{}',{})".format(
                        inbound_msg.cmd,
                        inbound_msg.num
                    )
                    logger.info(f"  [x] Query generated {query}, sending to db worker...")
                    response = await self.rmq_client.call(query,msg.correlation_id)
                    # async with response:
                    response = json.loads(response.decode())
                    logger.info("  [x] Response to query received: {}".format(response))
                    if response['success']:
                        reply = workerChar_pb2.msgreply(
                            response = "Command {} with num {} successful! ({})".format(
                                inbound_msg.cmd,
                                inbound_msg.num,
                                json.dumps(response)
                            ),
                            outcome=True
                        )
                    else:
                        reply = workerChar_pb2.msgreply(
                            response = "Command {} with num {} failed!: {}".format(
                                inbound_msg.cmd,
                                inbound_msg.num,
                                json.dumps(response)
                            ),
                            outcome=False
                        )
                    await self.exchange.publish(
                        Message(
                            body=reply.SerializeToString(),
                            correlation_id=msg.correlation_id
                        ),
                        routing_key=msg.reply_to
                    )
                    logging.info(' [x] Processed Request')
                except Exception:
                    logging.exception(" [!] Error processing for message: {}".format(msg))


if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerchar')
    asyncio.run(worker.run())