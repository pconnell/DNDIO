#/bin/sh

# pull down all the appropriate files from metadata
cd /home
mkdir shared
groupadd SharedUsers
chgrp -R SharedUsers /home/shared
chmod -R 2775 /home/shared
usermod -a -G SharedUsers pconn
usermod -a -G SharedUsers paco2756
cd shared

curl http://metadata/computeMetadata/v1/instance/attributes/init_stress -H "Metadata-Flavor: Google" > init_stress.py
curl http://metadata/computeMetadata/v1/instance/attributes/init_pb2 -H "Metadata-Flavor: Google" > workerInit_pb2.py
curl http://metadata/computeMetadata/v1/instance/attributes/init_grpc -H "Metadata-Flavor: Google" > workerInit_pb2_gprc.py

curl http://metadata/computeMetadata/v1/instance/attributes/char_stress -H "Metadata-Flavor: Google" > Char_stress.py
curl http://metadata/computeMetadata/v1/instance/attributes/char_pb2 -H "Metadata-Flavor: Google" > workerChar_pb2.py
curl http://metadata/computeMetadata/v1/instance/attributes/char_grpc -H "Metadata-Flavor: Google" > workerChar_pb2_gprc.py

curl http://metadata/computeMetadata/v1/instance/attributes/lookup_stress -H "Metadata-Flavor: Google" > Lookup_stress.py
curl http://metadata/computeMetadata/v1/instance/attributes/lookup_pb2 -H "Metadata-Flavor: Google" > workerLookup_pb2.py
curl http://metadata/computeMetadata/v1/instance/attributes/lookup_grpc -H "Metadata-Flavor: Google" > workerLookup_pb2_gprc.py

curl http://metadata/computeMetadata/v1/instance/attributes/roll_stress -H "Metadata-Flavor: Google" > Roll_stress.py
curl http://metadata/computeMetadata/v1/instance/attributes/roll_pb2 -H "Metadata-Flavor: Google" > workerRoll_pb2.py
curl http://metadata/computeMetadata/v1/instance/attributes/roll_grpc -H "Metadata-Flavor: Google" > workerRoll_pb2_gprc.py

curl http://metadata/computeMetadata/v1/instance/attributes/auth_token -H "Metadata-Flavor: Google" > auth_token.json

sudo apt-get update

sudo apt-get install -y python3 python3-pip git

sudo pip3 install grpcio grpcio-tools google-cloud-storage 

# potentially multi-threaded run 

    # stress test services

    # capture input and output messages

    # capture time delay between input and output

    # capture whether or not the reply was an error

    # store all captures to csvs

# multiple tests

    # time delay of .1 seconds between commands

    # time delay of 0.5 seconds between commands

    # no time delay