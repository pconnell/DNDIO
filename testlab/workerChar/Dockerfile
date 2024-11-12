FROM python:3.8
RUN apt update && apt install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-pip

#install necessaary dependencies...

RUN pip3 install pika grpcio grpcio-tools 

WORKDIR /app

COPY workerChar.py /app/workerChar.py

COPY dummy.py /app/dummy.py

COPY workerChar_pb2.py /app/workerChar_pb2.py

COPY workerChar_pb2_grpc.py /app/workerChar_pb2_grpc.py

# RUN cp ../protobufs/workerChar_pb2_grpc.py /app/workerChar_pb2_grpc.py

# RUN cp ../protobufs/workerChar_pb2.py /app/workerChar_pb2.py

# CMD ["/bin/bash"]

CMD ["python3", "workerChar.py"]