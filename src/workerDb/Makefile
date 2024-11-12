VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerDb
push:
	docker tag workerDb $(DOCKERUSER)/workerDb:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag workerDb$(DOCKERUSER)/workerDb:latest
	docker push $(DOCKERUSER)/workerDb:latest
