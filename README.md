```bash
  python3 -m grpc_tools.protoc \
    -I proto \
    --python_out=src/app/proto_generated \
    --grpc_python_out=src/app/proto_generated \
    proto/hltv.proto
```