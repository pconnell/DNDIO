import logging, base64, jsonpickle, io
import redis, json, os, hashlib

import requests, base64, json, os, glob, subprocess, jsonpickle

print("launching cluster to the cloud")
cmds = [
    "gcloud config set project lab5-paco2756",
    #machine type may need updating...
    "gcloud container clusters create lab7kube --release-channel None --zone us-central1-b --machine-type n2-standard-2",
    "gcloud container clusters get-credentials lab7kube --region us-central1-b",
    "kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.4/deploy/static/provider/cloud/deploy.yaml",
    #deploy message handler
    "kubectl apply -f ../redis/redis-deployment.yaml",
    "kubectl apply -f ../redis/redis-service.yaml",
    #deploy cassandra database
    "kubectl apply -f db/"
    #deploy rest server
    "kubectl apply -f ../rest/rest-deployment.yaml",
    "kubectl apply -f ../rest/rest-ingress.yaml",
    "kubectl apply -f ../rest/rest-service.yaml"
    #deploy worker services
    "kubectl apply -f ../workerChar/workerChar-deployment.yaml",
    "kubectl apply -f ../workerInit/workerInit-deployment.yaml",
    "kubectl apply -f ../workerLookup/workerLookup-deployment.yaml",
    "kubectl apply -f ../workerRoll/workerRoll-deployment.yaml"
]

for cmd in cmds[:-1]:
    print(cmd.split(' '))
    subprocess.run(cmd.split(' '))