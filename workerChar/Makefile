VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerChar
push:
	docker tag workerChar $(DOCKERUSER)/workerChar:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag workerChar$(DOCKERUSER)/workerChar:latest
	docker push $(DOCKERUSER)/workerChar:latest
