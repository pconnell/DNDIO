#/bin/sh
#run me when files in the protobuf_spec folder gets updated
python3 -m grpc_tools.protoc -I../protobuf_spec --python_out=. --pyi_out=. --grpc_python_out=. ../protobuf_spec/*.proto