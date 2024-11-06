VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t cass-db
push:
	docker tag cass-db $(DOCKERUSER)/cass-db:$(VERSION)
	docker push $(DOCKERUSER)/cass-db:$(VERSION)
	docker tag cass-db$(DOCKERUSER)/cass-db:latest
	docker push $(DOCKERUSER)/cass-db:latest
