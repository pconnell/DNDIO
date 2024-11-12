import redis,os
import subprocess as sub
import cassandra
from google.cloud import storage
from protobufs import workerInit_pb2
from protobufs import workerChar_pb2_grpc

REDIS_SERVICE_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_SERVICE_PORT = os.getenv('REDIS_PORT') or '6379'
storage_client = storage.Client.from_service_account_json('/app/lab5-paco2756.json')

def get_work():
    pass

def init_channel(channel_name, channel_users:list):
    #create an entry for a campaign and bind to channel in db

    #create characters in character db with no names and no stats

    #
    pass

while True:
    w = get_work()
    init_channel(w['channel'],w['channel_users'])