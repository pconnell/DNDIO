
import workerChar_pb2,workerChar_pb2_grpc,grpc
import argparse, shlex

def doInsertQuery(
        stub:workerChar_pb2_grpc.sendmsgStub,
        cmd:str,
        num:int,
        debug=False):
    # do some pre-processing of the command...
    data = workerChar_pb2.msg(
        cmd=cmd,
        num=num
    )
    if debug:
        print('sending command to server with cmd={} and num={}'.format(
            data.cmd,data.num
        ))
    reply = stub.sendmsg(data)
    return reply

def doGetQuery(
        stub:workerChar_pb2_grpc.sendmsgStub,
        cmd:str,
        debug=False):
    # do some pre-processing of the command...
    data = workerChar_pb2.msg(
        cmd=cmd,
        num=0
    )
    if debug:
        print('sending command to server with cmd={} and num={}'.format(
            data.cmd,data.num
        ))
    reply = stub.sendmsg(data)
    return reply

##steps to handle TLS requirements with ingress...
with open('../rest/tls.crt', 'rb') as f:
    cert_bytes = f.read()
credentials = grpc.ssl_channel_credentials(cert_bytes)
cert_cn = 'frontend.default.svc.cluster.local'
options = (('grpc.ssl_target_name_override', cert_cn,),)
channel = grpc.secure_channel('localhost:443', credentials, options)
stub = workerChar_pb2_grpc.sendmsgStub(channel)
import json
print(doInsertQuery(stub=stub,cmd="FULL FLEGED TEST",num=9001))