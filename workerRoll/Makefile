VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerRoll
push:
	docker tag workerRoll $(DOCKERUSER)/workerRoll:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag workerRoll$(DOCKERUSER)/workerRoll:latest
	docker push $(DOCKERUSER)/workerRoll:latest
