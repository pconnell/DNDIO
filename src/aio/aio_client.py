import asyncio
import logging
import random
import grpc
import workerChar_pb2, workerChar_pb2_grpc

# For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
CHANNEL_OPTIONS = [
    ("grpc.lb_policy_name", "pick_first"),
    ("grpc.enable_retries", 0),
    ("grpc.keepalive_timeout_ms", 10000),
]

async def run() -> None:
    async with grpc.aio.insecure_channel(
        target="localhost:5000", options=CHANNEL_OPTIONS
    ) as channel:
        stub = workerChar_pb2_grpc.sendmsgStub(channel)  #.GreeterStub(channel)
        # Timeout in seconds.
        # Please refer gRPC Python documents for more detail. https://grpc.io/grpc/python/grpc.html
        for i in range(1000):
            r = random.randint(1,101)
            msg = workerChar_pb2.msg(cmd="testing {}".format(r),num=i)
            response = await stub.sendmsg(
                msg,timeout=10
            )
            print("{}:{}".format(msg,response))

async def sec_run() -> None:
    with open('./tls.crt','rb') as f:
        cert_bytes = f.read()
        print(cert_bytes)
    # cert_bytes = open('./tls.crt','rb').read()
    credentials = grpc.ssl_channel_credentials(cert_bytes)
    cert_cn = 'rest.default.svc.cluster.local'
    options = (('grpc.ssl_target_name_override','cert_cn',),)
    async with grpc.aio.secure_channel(
        'localhost:443',
        credentials,
        options
    ) as channel:
        stub = workerChar_pb2_grpc.sendmsgStub(channel)
        for i in range(100):
            r = random.randint(9000,10000)
            msg = workerChar_pb2.msg(
                cmd='secure testing {}'.format(r),num=i
            )
            response = await stub.sendmsg(
                msg,timeout=30
            )
            print("{}:{}".format(msg,response))

if __name__ == "__main__":
    logging.basicConfig()
    # with open('./tls.crt','rb') as f:
    #     cert_bytes=f.read()
    # credentials = grpc.ssl_channel_credentials(cert_bytes)
    # cert_cn = 'frontend.default.svc.cluster.local'
    # options = (('grpc.ssl_target_name_override','cert_cn',),)
    # channel = grpc.secure_channel('localhost:443',credentials,options)
    # stub = workerChar_pb2_grpc.sendmsgStub(channel)
    # asyncio.run(sec_run())
    asyncio.run(sec_run())