VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t workerchar .
push:
	docker tag workerchar $(DOCKERUSER)/workerchar:$(VERSION)
	docker push $(DOCKERUSER)/workerchar:$(VERSION)
	docker tag workerchar $(DOCKERUSER)/workerchar:latest
	docker push $(DOCKERUSER)/workerchar:latest
