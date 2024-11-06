VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t rest-svr
push:
	docker tag rest-svr $(DOCKERUSER)/rest-svr:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag rest-svr$(DOCKERUSER)/rest-svr:latest
	docker push $(DOCKERUSER)/rest-svr:latest
