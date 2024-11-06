FROM python:3.8
RUN apt update && apt install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-pip
	
RUN pip3 install redis 

RUN pip3 install jsonpickle

WORKDIR /app

COPY rest-server.py /app/rest-server.py

CMD ["python3", "rest-server.py"]