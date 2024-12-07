import aio_pika,os,json,uuid,logging,sys
from cassandra.cluster import Cluster, PlainTextAuthProvider
from cassandra.cluster import (
    NoHostAvailable,
    OperationTimedOut
)
from cassandra.util import OrderedMapSerializedKey,SortedSet
from concurrent import futures
import uuid
from typing import MutableMapping
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)
from aio_pika import Message
import asyncio

RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or 5672
CASS_HOST = os.getenv('CASS_HOST') or 'localhost'
CASS_USER = os.getenv('CASS_USER') or 'cassandra'
CASS_PASS = os.getenv('CASS_PASS') or 'changeme'
CASS_DB = os.getenv('CASS_DB') or 'dndio'

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)

class cassDB():
    def __init__(self,user,pwd,host,db):
        self.auth_provider = PlainTextAuthProvider(
            username=user,
            password = pwd
        )
        self.host = host
        self.db = db
        self.cluster= None 
        self.session = None
        # self.connect()
    def connect(self):
        logger.info( " [x] Initializating DB Connection to Cassandra @ {}".format(self.host))
        self.cluster = Cluster(
            [self.host],
            auth_provider=self.auth_provider
        )
        logger.info("  [x] Establishing cluster session")
        self.session = self.cluster.connect()
        logger.info("  [x] Connecting to database: {}".format(self.db))
        self.session.set_keyspace(self.db)
        self.session.execute('USE {};'.format(self.db))
        logger.info( " [x] Connected to Cassandra Database!")

    def recurse_dict(self,d:OrderedMapSerializedKey):
        ret_d = {}
        for k,v in d.items():
            if isinstance(v,OrderedMapSerializedKey):
                ret_d[k] = self.recurse_dict(v)
            else:
                ret_d[k] = v
        return ret_d

    def rows_to_json(self,rows):
        result = []
        for row in rows:
            d = row._asdict()
            for k,v in d.items():
                if isinstance(v,uuid.UUID):
                    d[k] = str(v)
                if isinstance(v,OrderedMapSerializedKey):
                    d[k] = self.recurse_dict(v)
            result.append(d)
        return result

    # def parse_spells(self,rows):
    #     #convert data back to JSON/py dictionary
    #     for i in range(len(rows)):
    #         row = rows[i]
    #         dmg_dict = {}
    #         dmg = row['dmg']
    #         for level,dmgmap in dmg.items():
    #             dmg_dict[level] = {}
    #             for dmgtype,die_list in dmgmap.items():
    #                 dmg_dict[level][dmgtype] = []
    #                 for die in die_list:
    #                     dmg_dict[level][dmgtype].append(dict(die))
    #         upcast = dict(row['upcast'])
    #         curr_dict = rows[i].copy()
    #         curr_dict['upcast'] = upcast
    #         curr_dict['dmg']=dmg_dict
    #         rows[i] = curr_dict.copy()
    #     return rows

    # def parse_weapons(self,rows):
    #     #convert data back to JSON/py dictionary
    #     for i in range(len(rows)):
    #         row = rows[i]
    #         dmg_dict = {}
    #         dmg = row['dmg']
    #         for hands,dmgmap in dmg.items():
    #             dmg_dict[hands]={}
    #             for dmgtype,dice in dmgmap.items():
    #                 dmg_dict[hands][dmgtype] = dict(dice)
    #         curr_dict = row.copy()
    #         curr_dict['dmg'] = dmg_dict
    #         rows[i] = curr_dict.copy()
    #     return rows

    # ## parse out class data
    # def parse_class(self,rows):
    #     pass

    # ## parse out 

    # def _rows_to_json(self,rows):
    #     result = []
    #     for i in range(len(rows)):
    #         row = rows[i]
    #         d = row._asdict()
    #         for k,v in d.items():
    #             if isinstance(v,uuid.UUID):
    #                 d[k] = str(v)
    #         result.append(d)
    #     return result

    def exec_query(self,s):
        try:
            result = {
                'query':s,
                'success':False
            }
            try: 
                response = self.session.execute(s)
                result['success'] = True
            except NoHostAvailable:
                self.connect()
            except OperationTimedOut:
                self.connect()
            finally:
                if not result['success']:
                    response = self.session.execute(s)
                result['success'] = True
            logger.info("  [x] DB on_request: query succeeded: {}".format(s))
            l = response.all()
            result['success']= True
            result['rows'] = []
            logger.info(l)
            if len(l) > 0:
                result['rows'] = self.rows_to_json(l)
            return result
        except Exception as e:
            return {
                'query':s,
                'success':False,
                'msg':str(e)
            }

class rmq_server():
    def __init__(self,url,qname):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.qname = qname
        self.url = url
        self.db = cassDB(CASS_USER,CASS_PASS,CASS_HOST,CASS_DB)
        self.db.connect()

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
        logger.info(" [x] DB Worker Listining for RPC Requests")

    async def proc_err_msg(self,msg,err_msg):
        return {
            'query':msg.body.decode(),
            'success':False,
            'msg':err_msg
        }

    async def run(self):
        await self.connect()
        async with self.queue.iterator() as qiter:
            msg: AbstractIncomingMessage
            async for msg in qiter:
                try:
                    assert msg.reply_to is not None
                    logger.info("  [x] Received request: {}".format(msg))
                    q = msg.body.decode()
                    resp = self.db.exec_query(q)
                    logger.info("  [x] Received response: {}".format(resp))

                    await self.exchange.publish(
                        Message(
                            body=json.dumps(resp).encode(),
                            correlation_id=msg.correlation_id
                        ),
                        routing_key=msg.reply_to
                    )
                    logger.info(' [x] Processed Request')
                except Exception:
                    logger.exception(" [!] Error processing for message: {}".format(msg))

if __name__ == '__main__':
    listener = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'worker.db')
    asyncio.run(listener.run())
