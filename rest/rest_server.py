from flask import Flask, request, Response, send_file
import logging, base64, jsonpickle, io
import redis, json, os, hashlib

REDIS_SERVICE_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_SERVICE_PORT = os.getenv('REDIS_PORT') or '6379'

bucketname = 'toworker'
logbucket = 'logging'

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)
app = Flask(__name__)

r = redis.Redis(
    host=REDIS_SERVICE_HOST,
    port=REDIS_SERVICE_PORT
)

def lookup_response(args):
    pass

def roll_response(args):
    pass

def char_response(args):
    pass

@app.route('/apiv1/roll',methods=['GET'])
def roll():
    pass

@app.route('/apiv1/char',methods=['GET'])
def char():
    pass

@app.route('/apiv1/lookup',methods=['GET'])
def lookup():
    pass

@app.route('/apiv1/remove',methods=['GET'])
def remove_char():
    pass

@app.route('/apiv1/respond',methods=['GET'])
def respond():
    """ 
    used by workers to relay completion of a work request
    back to the appropriate discord channel
    
    - are response types needed?
    """
    pass

@app.route('/apiv1/workerlogs',methods=['GET'])
def get_logs():
    pass

def allMsgs(r,thread):
    data = [ x.decode('utf-8') for x in r.lrange(thread, 0, -1) ]
    return Response(json.dumps(data), mimetype="application/json")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)