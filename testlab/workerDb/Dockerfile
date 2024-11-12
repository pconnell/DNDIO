FROM python:3.8
RUN apt update && apt install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-pip

#install necessaary dependencies...

RUN pip3 install pika cassandra-driver grpcio grpcio-tools

WORKDIR /app

COPY workerDb.py /app/workerDb.py

COPY dummy.py /app/dummy.py

CMD ["python3", "workerDb.py"]

# CMD ["/bin/bash"]