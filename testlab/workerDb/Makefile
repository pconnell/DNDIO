VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerdb .

push:
	docker tag workerdb $(DOCKERUSER)/workerdb:$(VERSION)
	docker push $(DOCKERUSER)/workerdb:$(VERSION)
	docker tag workerdb $(DOCKERUSER)/workerdb:latest
	docker push $(DOCKERUSER)/workerdb:latest
