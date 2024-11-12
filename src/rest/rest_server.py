import logging, base64, jsonpickle, io
import redis, json, os, hashlib
from protobufs import (
    workerChar_pb2,
    workerChar_pb2_grpc,
    workerInit_pb2,
    workerInit_pb2_grpc,
    workerLookup_pb2,
    workerLookup_pb2_grpc,
    workerRoll_pb2,
    workerRoll_pb2_grpc
)
import grpc, pika, uuid

REDIS_SERVICE_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_SERVICE_PORT = os.getenv('REDIS_PORT') or '6379'

RMQ_SERVICE = os.getenv('RMQ_HOST')

bucketname = 'toworker'
logbucket = 'logging'

# r = redis.Redis(
#     host=REDIS_SERVICE_HOST,
#     port=REDIS_SERVICE_PORT
# )

class workerSetCharService(workerChar_pb2_grpc.getCharServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def setChar(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request #update
        )

        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )
        

class workerGetCharService(workerChar_pb2_grpc.setCharServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def getChar(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request #update
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerLookupService(workerInit_pb2_grpc.addServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def lookup(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerRollAttackService(workerRoll_pb2_grpc.rollAttackServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def roll(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerRollAttackDamageService(workerRoll_pb2_grpc.rollAttackDamageServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rollAttack(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )
    

class workerRollInitiativeService(workerRoll_pb2_grpc.rollInitiativeServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rollInitiative(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerRollSpellDamageService(workerRoll_pb2_grpc.rollSpellDamageServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rollSpellDamage(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerRollSpellcastService(workerRoll_pb2_grpc.rollSpellcastServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rollSpellcast(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

class workerRollSaveService(workerRoll_pb2_grpc.rollSaveServicer):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RMQ_SERVICE
            )
        )
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='',exclusive=True
        )
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self,ch,method,props,body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def rollSave(self,request,context):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key = 'workerSetCharREST',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ), 
            body = request
        )
        
        while self.response is None:
            self.connection.process_data_events()

        return workerChar_pb2.setcharreply(
            response = self.response
        )

def serve(d=False,v=False):
    s = grpc.server()
    workerChar_pb2_grpc.add_getCharServicer_to_server(
        workerSetCharService(),s
    )
    workerChar_pb2_grpc.add_getCharServicer_to_server(
        workerGetCharService(),s
    )
    workerLookup_pb2_grpc.add_lookupServicer_to_server(
        workerLookupService(),s
    )
    workerRoll_pb2_grpc.add_rollInitiativeServicer_to_server(
        workerRollInitiativeService(),s
    )
    workerRoll_pb2_grpc.add_rollAttackServicer_to_server(
        workerRollAttackService(),s
    )
    workerRoll_pb2_grpc.add_rollSpellcastServicer_to_server(
        workerRollSpellcastService(),s
    )
    workerRoll_pb2_grpc.add_rollAttackDamageServicer_to_server(
        workerRollAttackDamageService(),s
    )
    workerRoll_pb2_grpc.add_rollSpellDamageServicer_to_server(
        workerRollSpellDamageService(),s
    )

if __name__ == '__main__':
    channel = grpc.insecure_channel('localhost') #update
    funcs = {
        '':{
            'stub':workerChar_pb2_grpc.setCharStub(channel),
            'func':print
        },
        '':{
            'stub':workerChar_pb2_grpc.setCharStub(channel),
            'func':print
        }
    }
    pass