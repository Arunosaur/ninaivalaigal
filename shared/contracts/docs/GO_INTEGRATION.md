# Go Service Integration

**Purpose:** Protobuf + gRPC integration for Go services
**Status:** Future-Ready

---

## Quick Start (Future)

```go
// Install tools
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

// Generate code
protoc --go_out=. --go-grpc_out=. \
  ../../shared/contracts/graphops/v1/graphops.proto
```

```go
// main.go
package main

import (
    pb "ninaivalaigal/graphops/v1"
    "google.golang.org/grpc"
)

type server struct {
    pb.UnimplementedGraphOpsServiceServer
}

func (s *server) ExecuteQuery(ctx context.Context, req *pb.CypherRequest) (*pb.CypherResponse, error) {
    return &pb.CypherResponse{
        Results: []string{},
        ExecutionTimeMs: 0,
    }, nil
}
```

---

## Type Mappings

| Python | Protobuf | Go |
|--------|----------|-----|
| str | string | string |
| int | int32/int64 | int32/int64 |
| float | float/double | float32/float64 |
| bool | bool | bool |
| list | repeated | []T |

---

## References
- [gRPC-Go](https://grpc.io/docs/languages/go/)
