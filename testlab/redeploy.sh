kubectl delete deployment rest
kubectl delete deployment rabbitmq
kubectl delete deployment workerchar
kubectl delete deployment workerdb

cd rest
make build
make push

cd ../workerChar
make build
make push

cd ../workerDb
make build
make push

cd ..
output=$(pwd)
echo "$output"
kubectl apply -f $(pwd)/rabbitmq/rabbitmq-deployment.yaml
#kubectl apply -f /rabbitmq/rabbitmq-deployment.yaml
kubectl apply -f $(pwd)/rest/rest-deployment.yaml
kubectl apply -f $(pwd)/workerChar/workerChar-deployment.yaml
kubectl apply -f $(pwd)/workerDb/workerDb-deployment.yaml

#cd client
#python grpc_client.py
