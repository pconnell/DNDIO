FROM python:3.8
RUN apt update && apt install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-pip

#install necessaary dependencies...

RUN pip3 install pika grpcio grpcio-tools 

WORKDIR /app

COPY rest_server.py /app/rest_server.py

COPY workerChar_pb2.py /app/workerChar_pb2.py

COPY workerChar_pb2_grpc.py /app/workerChar_pb2_grpc.py

CMD ["python3", "rest_server.py", "-d","-v"]