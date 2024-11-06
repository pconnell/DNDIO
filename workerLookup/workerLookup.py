import redis,os
import subprocess as sub
import psycopg2 as pg
#cassandra?
from google.cloud import storage


REDIS_SERVICE_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_SERVICE_PORT = os.getenv('REDIS_PORT') or '6379'
storage_client = storage.Client.from_service_account_json('/app/lab5-paco2756.json')

def get_work():
    pass

def query():
    pass

while True:
    pass
