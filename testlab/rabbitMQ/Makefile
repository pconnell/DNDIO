VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t rabbit-mq
push:
	docker tag rabbit-mq $(DOCKERUSER)/rabbit-mq:$(VERSION)
	docker push $(DOCKERUSER)/rabbit-mq:$(VERSION)
	docker tag rabbit-mq$(DOCKERUSER)/rabbit-mq:latest
	docker push $(DOCKERUSER)/rabbit-mq:latest
