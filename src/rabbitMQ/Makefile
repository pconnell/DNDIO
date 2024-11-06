VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t redis-msg
push:
	docker tag redis-msg $(DOCKERUSER)/redis-msg:$(VERSION)
	docker push $(DOCKERUSER)/redis-msg:$(VERSION)
	docker tag redis-msg$(DOCKERUSER)/redis-msg:latest
	docker push $(DOCKERUSER)/redis-msg:latest
