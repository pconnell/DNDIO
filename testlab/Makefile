VERSION=v1
DOCKERUSER=pconnell89

all:
	make -C workerDb build
	make -C workerChar build
	make -C rest build
	make -C workerDb push
	make -C workerChar push
	make -C rest push

build-workerDb:
	docker build -f workerDb/Dockerfile -t workerdb workerDb/.

build-workerChar:
	docker build -f workerChar/Dockerfile -t workerchar workerChar/.

build-rest:
	docker build -f rest/Dockerfile -t rest rest/.

push-workerDb:
	docker tag workerdb $(DOCKERUSER)/workerdb:$(VERSION)
	docker push $(DOCKERUSER)/workerdb:$(VERSION)
	docker tag workerdb $(DOCKERUSER)/workerdb:latest
	docker push $(DOCKERUSER)/workerdb:latest

push-workerChar:
	docker tag workerchar $(DOCKERUSER)/workerchar:$(VERSION)
	docker push $(DOCKERUSER)/workerchar:$(VERSION)
	docker tag workerchar $(DOCKERUSER)/workerchar:latest
	docker push $(DOCKERUSER)/workerchar:latest

push-rest:
	docker tag testrest $(DOCKERUSER)/testrest:$(VERSION)
	docker push $(DOCKERUSER)/testrest:$(VERSION)
	docker tag testrest $(DOCKERUSER)/testrest:latest
	docker push $(DOCKERUSER)/testrest:latest

deploy-rabbitmq:
	kubectl apply -f ./rabbitmq/rabbitmq-deployment.yaml

deploy-workerDb:
	kubectl apply -f ./workerDb/workerDb-deployment.yaml

deploy-workerChar:
	kubectl apply -f ./workerChar/workerChar-deployment.yaml

deploy-rest:
	kubectl apply -f ./rest/rest-deployment.yaml

disable-rabbitmq:
	kubectl delete deployment rabbitmq

disable-rest:
	kubectl delete deployment rest

disable-workerDb:
	kubectl delete deployment workerdb

disable-workerChar:
	kubectl delete deployment workerchar

disable:
	kubectl delete deployment rest
	kubectl delete deployment workerchar
	kubectl delete deployment workerdb
	kubectl delete deployment rabbitmq

redeploy:
	kubectl delete -f ./workerDb/workerDb-deployment.yaml
	kubectl delete -f ./rest/rest-deployment.yaml
	kubectl delete -f ./workerChar/workerChar-deployment.yaml
	kubectl delete deployment rabbitmq
	kubectl apply -f ./rabbitmq/rabbitmq-deployment.yaml
	kubectl apply -f ./workerDb/workerDb-deployment.yaml
	kubectl apply -f ./rest/rest-deployment.yaml
	kubectl apply -f ./workerChar/workerChar-deployment.yaml

deploy:
	kubectl apply -f ./rabbitmq/rabbitmq-deployment.yaml
	kubectl apply -f ./workerDb/workerDb-deployment.yaml
	kubectl apply -f ./workerChar/workerChar-deployment.yaml
	kubectl apply -f ./rest/rest-deployment.yaml
