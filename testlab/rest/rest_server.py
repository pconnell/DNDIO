import argparse, os, grpc, pika, uuid

import pika.exceptions
# from protobufs import (
#     workerChar_pb2,
#     workerChar_pb2_grpc#,
    # workerInit_pb2,
    # workerInit_pb2_grpc,
    # workerRoll_pb2,
    # workerRoll_pb2_grpc,
    # workerLookup_pb2,
    # workerLookup_pb2_grpc
# )
import workerChar_pb2,workerChar_pb2_grpc
from concurrent import futures
import logging,sys

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)

RMQ_HOST = os.getenv('RMQ_HOST')
RMQ_PORT = os.getenv('RMQ_PORT')

class workerClient(object):
    def __init__(self,queue):
        self.queue = queue
        self.connection=None
        self.channel = None
        self.callback_queue = None
        self.connect(queue)
        # self.queue = queue
        # self.connection = pika.BlockingConnection(
        #     pika.ConnectionParameters(host=RMQ_HOST)
        # )
        # self.channel = self.connection.channel()
        # result = self.channel.queue_declare('',exclusive=True)
        # self.callback_queue = result.method.queue
        # self.channel.basic_consume(
        #     queue=self.callback_queue,
        #     on_message_callback=self.on_response,
        #     auto_ack=True
        # )

    def on_response(self,ch,method,props,body):
        logger.info("received response, checking...")
        if self.corr_id==props.correlation_id:
            logger.info('match found, setting response')
            self.response=body

    def call(self,queryStr):
        # self.response = None
        # self.corr_id = str(uuid.uuid4())
        # self.channel.basic_publish(
        #     exchange='',
        #     routing_key=self.queue,
        #     properties=pika.BasicProperties(
        #         reply_to=self.callback_queue,
        #         correlation_id=self.corr_id
        #     ),
        #     body = queryStr
        # )
        # while self.response is None:
        #     self.connection.process_data_events()
        # logger.info('returning response...{}'.format(self.response))
        # return self.response
        try: 
            return self._call(queryStr)
        except pika.exceptions.ConnectionClosed:
            logger.error('error: connection to RabbitMQ closed. Reconnecting...')
            self.connect()
        except pika.exceptions.ConnectionWrongStateError:
            logger.error('error: connection in incorrect state, reconnecting...')
            self.connect()
        finally: 
            logger.info('connection to RabbitMQ re-established! Calling...')
            return self._call(queryStr)

    def _call(self,queryStr):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        logger.info('publishing message to queue: {}'.format(self.queue))
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body = queryStr
        )
        while self.response is None:
            self.connection.process_data_events()
        logger.info('returning response...{}'.format(self.response))
        return self.response

    def connect(self,queue):
        if not self.connection or self.connection.is_closed:
            self.queue = queue
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RMQ_HOST)
            )
            self.channel = self.connection.channel()
            result = self.channel.queue_declare('',exclusive=True)
            self.callback_queue = result.method.queue
            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True
            )

class workerCharService(workerChar_pb2_grpc.sendmsgServicer):
    def __init__(self,debug=False,verbose=False):
        self.debug = debug
        self.verbose = verbose
        self.queue = workerClient('worker_rest')

    def sendmsg(self,request,context):
        logger.info("received request, calling...")
        print(request)
        msg = workerChar_pb2.msg()
        if isinstance(request,workerChar_pb2.msg):
            print(request)
            msg=request.SerializeToString()
        else:
            logger.info("wrong type...")
            print("wrong type")
        print(msg)
        response = self.queue.call(msg)
        logger.info("recieved reply...parsing")
        reply = workerChar_pb2.msgreply()
        reply.ParseFromString(response)
        logger.info("sending reply...")
        return reply

# class workerRollService(workerChar_pb2_grpc.sendmsgServicer):
#     def __init__(self,debug=False,verbose=False):
#         self.debug = debug
#         self.verbose = verbose
#         self.queue = workerClient('workerRoll_rest')

#     def processMsg(self,request,context):
#         response = self.queue.call(request)
#         reply = workerChar_pb2.msgreply()
#         reply.ParseFromString(response)
#         return reply

# class workerInitService(workerChar_pb2_grpc.sendmsgServicer):
#     def __init__(self,debug=False,verbose=False):
#         self.debug = debug
#         self.verbose = verbose
#         self.queue = workerClient('workerInit_rest')

#     def processMsg(self,request,context):
#         response = self.queue.call(request)
#         reply = workerChar_pb2.msgreply()
#         reply.ParseFromString(response)
#         return reply

# class workerLookupService(workerChar_pb2_grpc.sendmsgServicer):
#     def __init__(self,debug=False,verbose=False):
#         self.debug = debug
#         self.verbose = verbose
#         self.queue = workerClient('workerLookup_rest')

#     def processMsg(self,request,context):
#         response = self.queue.call(request)
#         reply = workerChar_pb2.msgreply()
#         reply.ParseFromString(response)
#         return reply

def serve(d=False,v=False):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=500)) #?
    workerChar_pb2_grpc.add_sendmsgServicer_to_server(
        workerCharService(debug=d,verbose=v),server
    )
    # workerInit_pb2_grpc.add_sendmsgServicer_to_server(
    #     workerInitService(debug=d,verbose=v),server
    # )
    # workerRoll_pb2_grpc.add_sendmsgServicer_to_server(
    #     workerRollService(debug=d,verbose=v),server
    # )
    # workerLookup_pb2_grpc.add_sendmsgServicer_to_server(
    #     workerLookupService(debug=d,verbose=v),server
    # )
    logger.info(" [x] Adding listener port on 5000")
    server.add_insecure_port('[::]:5000')
    logger.info(" [x] Starting server...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logger.info('[x] Starting applicationo')
    parser =argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-v','--verbose',action='store_true',
        help="include verbose debug outputs",
    )

    parser.add_argument(
        '-d','--debug',action='store_true',
        help="include basic debug outputs"
    )
    logger.info('parsing args')
    args = parser.parse_args()

    serve(args.debug,args.verbose) 