import redis,os
import subprocess as sub
# import psycopg2 as pg
from google.cloud import storage
from protobufs import workerChar_pb2
from protobufs import workerChar_pb2_grpc
import argparse, shlex

REDIS_SERVICE_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_SERVICE_PORT = os.getenv('REDIS_PORT') or '6379'
# storage_client = storage.Client.from_service_account_json('/app/lab5-paco2756.json')
r = redis.Redis(
    host=REDIS_SERVICE_HOST,
    port=REDIS_SERVICE_PORT
)
get_parser = argparse.ArgumentParser(description='blah')
get_parser.add_argument('') #stats

##example of set character parsing
s="""
    --stat CHR=12 --stat STR=13 --stat INT=9 --stat CON=14 --stat WIS=10 --stat DEX=18
    --proficiency_bonus 2
    --skill name=value --skill name2=value2 
    --AC 12
    --class Warlock
    --spellDC 15
    --level 5
    --race Dragonborn
    --spells add="Eldrich Blast" --spells add="Hex" --spells add="Hellish Rebuke"
    --spellslots 1=4 --spellslots 2=3
    --spellcast_ability CHR
    --name "STRING"
"""
v = shlex.split(s)
set_parser = argparse.ArgumentParser(description="blah2")
set_parser.add_argument('--stat',metavar='KEY=VALUE',action='append')
set_parser.add_argument('--proficiency_bonus',action='store')
set_parser.add_argument('--primary_skill',action='append')
set_parser.add_argument('--AC',action='store')
set_parser.add_argument('--class',action='store')
set_parser.add_argument('--race',action='store')
set_parser.add_argument('--level',action='store')
#add=SPELL, remove=SPELL
set_parser.add_argument('--spells',metavar="KEY=VALUE",action='append')
set_parser.add_argument('--skill',metavar="KEY=VALUE",action='append')
set_parser.add_argument('--name',action='store')
set_parser.add_argument('--spellDC',action='store')
#[level]=[qty], [level]=[qty],...
set_parser.add_argument('--spellslots',metavar="KEY=VALUE",action='append')
set_parser.add_argument('--spellcast_ability',metavar="KEY=VALUE",action='append')
set_parser.add_argument('--inv',action='append')
vars(set_parser.parse_args(v))
get_group =get_parser.add_mutually_exclusive_group()
get_group.add_argument('-b','--baseState',action='store_true',default=False)
get_group.add_argument('-c','--currState',action='store_true',default=False)
get_group.add_argument('--stats', action='store_true',default=False)
get_group.add_argument('--skills',action='store_true',default=False)
get_group.add_argument('--spells', action='store_true',default=False)
get_group.add_argument('--spellslots',action='store_true',default=False)
get_group.add_argument('--weapons',action='store_true',default=False)
get_group.add_argument('--name',action='store_true',default=False)
s = """ 
--stats
"""
v = shlex.split(s)
vars(get_parser.parse_args(v))

class charGetSvc(workerChar_pb2_grpc.getCharServicer):
    def __init__(self):
        pass 

    def charGet(self,request):
        cmd = request.cmd
        args = request.args
        channel = request.channel
        user = request.user
        #parse the args
        
        #decide which helper function to use

        #call the helper function

        #await the reply from the helper

        #build the response and send it
        return workerChar_pb2.getcharreply(
            response=''
        )

    pass

class charSetSvc(workerChar_pb2_grpc.setCharServicer):
    def __init__(self):
        pass

    def charSet(self,request):
        channel = request.channel
        user = request.user
        cmd = request.cmd
        args = request.args
        #parse the args
        dat = vars(set_parser.parse_args(user))
        query_str = "UPDATE DNDIO.character "
        for k in dat.keys():
            if dat.get(k,None):
                if isinstance(dat[k],list):
                    #append everything
                    for item in dat[k]:
                        query_str+='SET ' #don't know...
                else:
                    query_str+="SET {}={}\n".format(k,dat[k])
                    #append the one

        query_str += 'WHERE user={} AND channel={};'.format(user,channel)
        #send the item to the message queue

        #wait for the response

        #build the response and send it
        resp = workerChar_pb2.setcharreply(
            response = ''
        )
        r.rpush('workerCharREST',resp)
        