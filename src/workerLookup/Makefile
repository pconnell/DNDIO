VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerLookup
push:
	docker tag workerLookup $(DOCKERUSER)/workerLookup:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag workerLookup$(DOCKERUSER)/workerLookup:latest
	docker push $(DOCKERUSER)/workerLookup:latest
