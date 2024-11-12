import pika,os,json,uuid,logging,sys
from cassandra.cluster import Cluster, PlainTextAuthProvider
from cassandra.cluster import (
    NoHostAvailable,
    OperationTimedOut
)
import pika.exceptions

RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or 5672
CASS_DB = os.getenv('CASS_HOST') or 'localhost'
CASS_USER = os.getenv('CASS_USER') or 'cassandra'
CASS_PASS = os.getenv('CASS_PASS') or 'changeme'

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)



connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RMQ_HOST)
)

channel = connection.channel()
channel.queue_declare('worker_db')

auth_provider = PlainTextAuthProvider(
    username=CASS_USER,
    password=CASS_PASS
)
cluster = Cluster([CASS_DB],auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace('dndio')
session.execute('USE DNDIO') 

def connectRMQ():
    global connection
    global channel
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare('worker_db')

def connectCassDB():
    global auth_provider
    global cluster
    global session
    auth_provider = PlainTextAuthProvider(
        username=CASS_USER,
        password=CASS_PASS
    )
    cluster = Cluster([CASS_DB],auth_provider=auth_provider)
    session = cluster.connect()
    session.set_keyspace('dndio')
    session.execute('USE DNDIO') 

def rows_to_json(rows):
    result = []
    for row in rows:
        #print(row)
        d = row._asdict()
        #print(d)
        for k,v in d.items():
            #print(type(v))
            if isinstance(v,uuid.UUID):
                d[k] = str(v)
            result.append(d)
    return result

def emit_response(ch,method,props,body):
    logger.info('responding to query request...')
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(
            correlation_id=props.correlation_id
        ),
        body=body
    )

def on_request(ch,method,props,body):
    s = body.decode('utf-8')
    #print(s)
    result = {
        'query':s,
        'success':False
    }
    try: 
        try:
            response = session.execute(s)
        except NoHostAvailable:
            connectCassDB()
            pass 
        except OperationTimedOut:
            connectCassDB()
        finally: 
            response = session.execute(s)
        
        logger.info("on_request: query succeeded: {}".format(s))
        l = [r for r in response]
        result['success'] = True
        if len(l) > 0:
            logger.info("converting rows to json response...")
            result['rows'] = rows_to_json(l)
    except:
        logger.error("on_request: query failed to execute: {}".format(s))
        result['success'] = False 

    finally:
        # try:
        # emit_response(ch,method,props,json.dumps(result))

        logger.info('repsonding to query request...')
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id
            ),
            body=json.dumps(result)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        # except pika.exceptions.ConnectionClosed:
        #     logger.error('error: connection to RabbitMQ closed. Reconnecting...')
        #     connectRMQ()
        # except pika.exceptions.ConnectionWrongStateError:
        #     logger.error('error: connection in incorrect state, reconnecting...')
        #     connectRMQ()
        # finally:
        #     emit_response(ch,method,props,json.dumps(result))
            # logger.info('responding to query request...')
            # ch.basic_publish(
            #     exchange='',
            #     routing_key=props.reply_to,
            #     properties=pika.BasicProperties(
            #         correlation_id=props.correlation_id
            #     ),
            #     body=json.dumps(result)
            # )
            # ch.basic_ack(delivery_tag=method.delivery_tag)
        # pass

if __name__ == '__main__':
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='worker_db',on_message_callback=on_request)
    logger.info(" [x] Awaiting RPC Requests")
    channel.start_consuming()
