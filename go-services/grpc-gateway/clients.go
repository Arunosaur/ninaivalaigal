package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"

	// Import generated gRPC clients
	graphopspb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/graphopspb"
	memorypb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/memorypb"
)

// gRPC client manager
type GRPCClients struct {
	// Memory service client
	MemoryClient memorypb.MemoryServiceClient
	memoryConn   *grpc.ClientConn

	// GraphOps service client
	GraphOpsClient graphopspb.GraphOpsServiceClient
	graphOpsConn   *grpc.ClientConn
}

// Initialize all gRPC client connections
func NewGRPCClients() (*GRPCClients, error) {
	clients := &GRPCClients{}

	// Setup connection options
	opts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second, // send pings every 10 seconds if there is no activity
			Timeout:             time.Second,      // wait 1 second for ping ack before considering the connection dead
			PermitWithoutStream: true,             // send pings even without active streams
		}),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(4*1024*1024), // 4MB max message size
			grpc.MaxCallSendMsgSize(4*1024*1024),
		),
	}

	// Connect to Memory Service
	log.Printf("🔗 Connecting to Memory Service at %s", MemoryAddr)
	memoryConn, err := grpc.NewClient(MemoryAddr, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to memory service: %w", err)
	}
	clients.memoryConn = memoryConn
	clients.MemoryClient = memorypb.NewMemoryServiceClient(memoryConn)

	// Connect to GraphOps Service
	log.Printf("🔗 Connecting to GraphOps Service at %s", GraphOpsAddr)
	graphOpsConn, err := grpc.NewClient(GraphOpsAddr, opts...)
	if err != nil {
		if closeErr := memoryConn.Close(); closeErr != nil {
			log.Printf("⚠️ Failed to close memory connection: %v", closeErr)
		}
		return nil, fmt.Errorf("failed to connect to graphops service: %w", err)
	}
	clients.graphOpsConn = graphOpsConn
	clients.GraphOpsClient = graphopspb.NewGraphOpsServiceClient(graphOpsConn)

	// Test connections with health checks
	if err := clients.testConnections(); err != nil {
		clients.Close()
		return nil, fmt.Errorf("connection health check failed: %w", err)
	}

	log.Println("✅ All gRPC connections established successfully")
	return clients, nil
}

// Test all gRPC connections with health checks
func (c *GRPCClients) testConnections() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Test Memory Service connection
	if err := c.testMemoryConnection(ctx); err != nil {
		return fmt.Errorf("memory service connection test failed: %w", err)
	}

	// Test GraphOps Service connection
	if err := c.testGraphOpsConnection(ctx); err != nil {
		return fmt.Errorf("graphops service connection test failed: %w", err)
	}

	return nil
}

// Test Memory Service connection
func (c *GRPCClients) testMemoryConnection(ctx context.Context) error {
	if c.MemoryClient == nil {
		log.Printf("⚠️  Memory Service client is nil (service may not be initialized)")
		return nil // Don't fail if client is not initialized
	}
	req := &memorypb.HealthCheckRequest{}
	resp, err := c.MemoryClient.HealthCheck(ctx, req)
	if err != nil {
		log.Printf("⚠️  Memory Service health check failed: %v (service may not be running)", err)
		return nil // Don't fail startup if service is not available
	}
	log.Printf("✅ Memory Service health: %s", resp.Status)
	return nil
}

// Test GraphOps Service connection
func (c *GRPCClients) testGraphOpsConnection(ctx context.Context) error {
	if c.GraphOpsClient == nil {
		log.Printf("⚠️  GraphOps Service client is nil (service may not be initialized)")
		return nil // Don't fail if client is not initialized
	}
	req := &graphopspb.HealthCheckRequest{}
	resp, err := c.GraphOpsClient.HealthCheck(ctx, req)
	if err != nil {
		log.Printf("⚠️  GraphOps Service health check failed: %v (service may not be running)", err)
		return nil // Don't fail startup if service is not available
	}
	log.Printf("✅ GraphOps Service health: %s", resp.Status)
	return nil
}

// Close all gRPC connections
func (c *GRPCClients) Close() {
	if c.memoryConn != nil {
		log.Println("🔌 Closing Memory Service connection")
		if err := c.memoryConn.Close(); err != nil {
			log.Printf("⚠️ Failed to close memory connection: %v", err)
		}
	}

	if c.graphOpsConn != nil {
		log.Println("🔌 Closing GraphOps Service connection")
		if err := c.graphOpsConn.Close(); err != nil {
			log.Printf("⚠️ Failed to close graphops connection: %v", err)
		}
	}
}

// Connection status for health endpoint
func (c *GRPCClients) GetConnectionStatus() map[string]string {
	status := make(map[string]string)

	// Check Memory Service connection
	if c.memoryConn != nil {
		state := c.memoryConn.GetState()
		status["memory_service"] = fmt.Sprintf("%s (%s)", MemoryAddr, state.String())
	} else {
		status["memory_service"] = "disconnected"
	}

	// Check GraphOps Service connection
	if c.graphOpsConn != nil {
		state := c.graphOpsConn.GetState()
		status["graphops_service"] = fmt.Sprintf("%s (%s)", GraphOpsAddr, state.String())
	} else {
		status["graphops_service"] = "disconnected"
	}

	return status
}
