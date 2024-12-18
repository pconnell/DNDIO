VERSION=v1
DOCKERUSER=pconnell89

protobufs:
	python3 -m grpc_tools.protoc -I./protobuf_spec --python_out=. --grpc_python_out=. ./protobuf_spec/*.proto

grpc-build:
	cp ../discord/dndio_pb2_grpc.py .
	cp ../discord/dndio_pb2.py .
	docker build -f grpc-Dockerfile -t grpctest .
	rm ./dndio_pb2.py
	rm ./dndio_pb2_grpc.py 

db-build:
	docker build -f db-Dockerfile -t dbworker .

char-build:
	cp ../discord/dndio_pb2_grpc.py .
	cp ../discord/dndio_pb2.py .
	docker build -f char-Dockerfile -t charworker .
	rm ./dndio_pb2.py
	rm ./dndio_pb2_grpc.py 

init-build:
	cp ../discord/dndio_pb2_grpc.py .
	cp ../discord/dndio_pb2.py .
	docker build -f init-Dockerfile -t initworker .
	rm ./dndio_pb2.py
	rm ./dndio_pb2_grpc.py 

roll-build: 
	cp ../discord/dndio_pb2_grpc.py .
	cp ../discord/dndio_pb2.py .
	docker build -f roll-Dockerfile -t rollworker .
	rm ./dndio_pb2.py
	rm ./dndio_pb2_grpc.py 

lookup-build:
	cp ../discord/dndio_pb2_grpc.py .
	cp ../discord/dndio_pb2.py .
	docker build -f lookup-Dockerfile -t lookupworker .
	rm ./dndio_pb2.py
	rm ./dndio_pb2_grpc.py 
	
pull:
	docker pull pconnell89/grpctest
	docker pull pconnell89/dbworker
	docker pull pconnell89/charworker
	docker pull pconnell89/initworker
	docker pull pconnell89/rollworker
	docker pull pconnell89/lookupworker

build:
	make grpc-build
	make db-build
	make char-build
	make init-build
	make roll-build 
	make lookup-build

grpc-push:
	docker tag grpctest $(DOCKERUSER)/grpctest:$(VERSION)
	docker push $(DOCKERUSER)/grpctest:$(VERSION)
	docker tag grpctest $(DOCKERUSER)/grpctest:latest
	docker push $(DOCKERUSER)/grpctest:latest

db-push:
	docker tag dbworker $(DOCKERUSER)/dbworker:$(VERSION)
	docker push $(DOCKERUSER)/dbworker:$(VERSION)
	docker tag dbworker $(DOCKERUSER)/dbworker:latest
	docker push $(DOCKERUSER)/dbworker:latest

char-push:
	docker tag charworker $(DOCKERUSER)/charworker:$(VERSION)
	docker push $(DOCKERUSER)/charworker:$(VERSION)
	docker tag charworker $(DOCKERUSER)/charworker:latest
	docker push $(DOCKERUSER)/charworker:latest

init-push:
	docker tag initworker $(DOCKERUSER)/initworker:$(VERSION)
	docker push $(DOCKERUSER)/initworker:$(VERSION)
	docker tag initworker $(DOCKERUSER)/initworker:latest
	docker push $(DOCKERUSER)/initworker:latest

roll-push:
	docker tag rollworker $(DOCKERUSER)/rollworker:$(VERSION)
	docker push $(DOCKERUSER)/rollworker:$(VERSION)
	docker tag rollworker $(DOCKERUSER)/rollworker:latest
	docker push $(DOCKERUSER)/rollworker:latest

lookup-push:
	docker tag lookupworker $(DOCKERUSER)/lookupworker:$(VERSION)
	docker push $(DOCKERUSER)/lookupworker:$(VERSION)
	docker tag lookupworker $(DOCKERUSER)/lookupworker:latest
	docker push $(DOCKERUSER)/lookupworker:latest

push:
	make grpc-push
	make db-push
	make char-push
	make init-push
	make roll-push
	make lookup-push

grpc-deploy:
	kubectl apply -f rest-deployment.yaml
	kubectl apply -f rest-ingress.yaml
	kubectl apply -f rest-service.yaml

db-deploy:
	kubectl apply -f workerDb-deployment.yaml

char-deploy:
	kubectl apply -f workerChar-deployment.yaml

rmq-deploy:
	kubectl apply -f rabbitmq-deployment.yaml
	kubectl apply -f rabbitmq-service.yaml

init-deploy:
	kubectl apply -f workerInit-deployment.yaml

roll-deploy:
	kubectl apply -f workerRoll-deployment.yaml

lookup-deploy:
	kubectl apply -f workerLookup-deployment.yaml

deploy:
	make rmq-deploy 
	make grpc-deploy
	make db-deploy
	make char-deploy
	make init-deploy
	make roll-deploy
	make lookup-deploy
	kubectl expose deployment ingress-nginx-controller --type=LoadBalancer -n ingress-nginx --name ingress-nginx-service --external_ip='192.168.0.110' --port=44443 --protocol TCP

grpc-disable:
	kubectl delete -f rest-deployment.yaml

db-disable:
	kubectl delete -f workerDb-deployment.yaml

char-disable:
	kubectl delete -f workerChar-deployment.yaml

rmq-disable:
	kubectl delete deployment rabbitmq
	kubectl delete service rabbitmq

init-disable:
	kubectl delete -f workerInit-deployment.yaml

roll-disable:
	kubectl delete -f workerRoll-deployment.yaml

lookup-disable:
	kubectl delete -f workerLookup-deployment.yaml

disable:
	make grpc-disable
	make db-disable
	make char-disable
	make rmq-disable
	make init-disable
	make roll-disable
	make lookup-disable