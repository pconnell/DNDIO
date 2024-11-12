import pika,os,argparse,shlex,subprocess as sub,uuid,json,sys

import pika.exceptions
import workerChar_pb2, workerChar_pb2_grpc,logging

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

class workerCharDbRabMQClient(object):
    def __init__(self,queue):
        # self.queue = queue
        # self.connection = None
        # self.channel = None
        # self.callback_queue = None
        # self.connect(queue)
        self.queue = queue
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RMQ_HOST)
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare('',exclusive=True)
        self.callback_queue = result.method.queue
        logger.debug('  [x] initialized rabbitMQ connection')
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        ) 

    def on_response(self,ch,method,props,body):
        logger.info("  [x] received response from DB...checking for match")
        if self.corr_id==props.correlation_id:
            logger.info('  [x] match found, setting response...')
            self.response=body

    def call(self,queryStr):
        # try:
        return self._call(queryStr)
        # except pika.exceptions.ConnectionClosed:
        #     logger.error('error: connection to RabbitMQ closed. Reconnecting...')
        #     self.connect()
        # except pika.exceptions.ConnectionWrongStateError:
        #     logger.error('error: connection in incorrect state, reconnecting...')
        #     self.connect()
        # finally:
        #     return self._call(queryStr)

    def _call(self,queryStr):
        logger.info('  [x] processing call request...{}'.format(queryStr))
        self.response = None
        self.corr_id = str(uuid.uuid4())
        logger.info('  [x] transmitting to workerdb queue...')
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body = queryStr
        )
        logger.info('  [x] awaiting response...')
        while self.response is None:
            self.connection.process_data_events()
        logger.info('  [x] received response...emitting...')
        return self.response
    
    # def connect(self,queue):
    #     if not self.connection or self.connection.is_closed:
    #         self.queue = queue
    #         self.connection = pika.BlockingConnection(
    #             pika.ConnectionParameters(host=RMQ_HOST)
    #         )
    #         self.channel = self.connection.channel()
    #         result = self.channel.queue_declare('',exclusive=True)
    #         self.callback_queue = result.method.queue
    #         self.channel.basic_consume(
    #             queue=self.callback_queue,
    #             on_message_callback=self.on_response,
    #             auto_ack=True
    #         )

# rabbitMQ = workerCharDbRabMQClient('worker_db')
# print(" [x] Requesting...")
# query='SELECT * FROM worker;'
# response = rabbitMQ.call(query)
################above here works##########################
class workerRESTRabMQServer(object):
    def __init__(self):
        # self.connection = None
        # self.channel=None
        # self.connect()
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RMQ_HOST)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare('worker_rest')
        self.DB_RMQ = workerCharDbRabMQClient('worker_db')

    def on_request(self,ch,method,props,body):
        logging.info('received request from rabbitMQ...parsing')
        logging.info(body)
        msg = workerChar_pb2.msg()
        msg.ParseFromString(body)
        logging.info('request parsed...generating query...')
        query = "INSERT INTO worker (id,cmd,num) VALUES (uuid(),'{}',{})".format(
            msg.cmd,msg.num
        )
        logging.info('query generated: {}, executing...'.format(query))
        try:
            response = self.DB_RMQ.call(query)
        except pika.exceptions.ConnectionClosed:
            logger.error('error: connection to RabbitMQ closed. Reconnecting...')
            self.connect()
        except pika.exceptions.ConnectionWrongStateError:
            logger.error('error: connection in incorrect state, reconnecting...')
            self.connect()
        finally:
            response = self.DB_RMQ.call(query)
        reply = None
        response = json.loads(response.decode('utf-8'))
        logging.info(response)
        if response['success']:
            reply = workerChar_pb2.msgreply(
                response = "Command {} with num {} successful! ({})".format(
                    msg.cmd,
                    msg.num,
                    json.dumps(response)
                ),
                outcome=True
            )
        else:
            reply = workerChar_pb2.msgreply(
                response = "Command {} with num {} failed!: {}".format(
                    msg.cmd,msg.num,
                    json.dumps(response)
                ),
                outcome=False
            )
        # try:
            # self._publish(method,props,reply)
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id
            ),
            body=reply.SerializeToString()
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # except pika.exceptions.ConnectionClosed:
        #     logger.error('error: connection to RabbitMQ closed. Reconnecting...')
        #     self.connect()
        # except pika.exceptions.ConnectionWrongStateError:
        #     logger.error('error: connection to RabbitMQ in incorrect state. Reconnecting...')
        #     self.connect()
        # finally:
        #     logger.info('connection to RabbitMQ re-established! Publishing...')
        #     self._publish(method,props,reply)

    def _publish(self,method,props,reply):
        self.channel.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id
            ),
            body=reply.SerializeToString()
        )
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RMQ_HOST)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare('worker_rest')
            self.DB_RMQ = workerCharDbRabMQClient('worker_db')

    def run(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='worker_rest',
            on_message_callback=self.on_request
        )
        logger.info(' [x] Awaiting RPC Requests...')
        # print(" [x] Awaiting RPC Requests")
        self.channel.start_consuming()

if __name__=='__main__':
    worker = workerRESTRabMQServer()
    worker.run()