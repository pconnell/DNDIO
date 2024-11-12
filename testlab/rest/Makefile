VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t testrest .
push:
	docker tag testrest $(DOCKERUSER)/testrest:$(VERSION)
	docker push $(DOCKERUSER)/testrest:$(VERSION)
	docker tag testrest $(DOCKERUSER)/testrest:latest
	docker push $(DOCKERUSER)/testrest:latest
