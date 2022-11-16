mkdir compiled_protobufs
python3 -m grpc_tools.protoc -I=./protobufs --python_out=./compiled_protobufs ./protobufs/asr_info.proto ./protobufs/taskmap.proto ./protobufs/semantic_searcher.proto
