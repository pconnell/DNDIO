VERSION=v1
DOCKERUSER=pconnell89

build:
	docker build -f Dockerfile -t demucs-worker .
push:
	docker tag demucs-worker $(DOCKERUSER)/demucs-worker:$(VERSION)
	docker push $(DOCKERUSER)/demucs-worker:$(VERSION)
	docker tag demucs-worker $(DOCKERUSER)/demucs-worker:latest
	docker push $(DOCKERUSER)/demucs-worker:latest

gkebuild:
	docker build -f gke-Dockerfile -t gke-demucs-worker2 .

gkepush:
	docker tag gke-demucs-worker2 $(DOCKERUSER)/gke-demucs-worker2:$(VERSION)
	docker push $(DOCKERUSER)/gke-demucs-worker2:$(VERSION)
	docker tag gke-demucs-worker2 $(DOCKERUSER)/gke-demucs-worker2:latest
	docker push $(DOCKERUSER)/gke-demucs-worker2:latest
run:
	docker run --rm -i \
		--name=demucs \
		-v $(current-dir)input:/data/input \
		-v $(current-dir)output:/data/output \
		-v $(current-dir)models:/data/models \
		xserrat/facebook-demucs:latest \
		"python3 -m demucs.separate --out /data/output \
		/data/input/$(track)"