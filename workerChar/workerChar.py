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

def get_file_from_storage(name):
    pass

def push_file_to_storage(name):
    pass

def get_data(channel,user,field):
    # lookup user character information / record from db 
    # based upon channel and user
    # return char information to API server
    # via callback?
    pass

def update_data(channel,user,field,value):
    # lookup user character information / record from db 
    #based upon channel and user
    # set the field to the value in the data base
    # return char information / confirmation to API server
    # via callback?
    pass

def gen_charsheet(channel,user):
    # lookup user character information / record from db 
    #based upon channel and user
    #create and populate a charactersheet pdf 
    #store in GKE bucket storage
    # return char information / confirmation to API server
    # via callback?
    pass

def init_char(channel,user):
    #do a die roll set for stat block
    #store them in char information
    
    pass

while True:
    w = get_work()
    func = {

    }[w['action']]
