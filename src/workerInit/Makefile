VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerInit
push:
	docker tag workerInit $(DOCKERUSER)/workerInit:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag workerInit$(DOCKERUSER)/workerInit:latest
	docker push $(DOCKERUSER)/workerInit:latest
