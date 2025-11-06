package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"google.golang.org/grpc"

	graphopspb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/graphopspb"
)

// Mock GraphOpsServiceClient for testing
type MockGraphOpsClient struct {
	ExecuteQueryFunc       func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error)
	ExecuteTransactionFunc func(ctx context.Context, in *graphopspb.ExecuteTransactionRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteTransactionResponse, error)
	HealthCheckFunc        func(ctx context.Context, in *graphopspb.HealthCheckRequest, opts ...grpc.CallOption) (*graphopspb.HealthCheckResponse, error)
	GetGraphStatsFunc      func(ctx context.Context, in *graphopspb.GetGraphStatsRequest, opts ...grpc.CallOption) (*graphopspb.GetGraphStatsResponse, error)
}

func (m *MockGraphOpsClient) ExecuteQuery(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
	if m.ExecuteQueryFunc != nil {
		return m.ExecuteQueryFunc(ctx, in, opts...)
	}
	return nil, nil
}

func (m *MockGraphOpsClient) ExecuteTransaction(ctx context.Context, in *graphopspb.ExecuteTransactionRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteTransactionResponse, error) {
	if m.ExecuteTransactionFunc != nil {
		return m.ExecuteTransactionFunc(ctx, in, opts...)
	}
	return nil, nil
}

func (m *MockGraphOpsClient) HealthCheck(ctx context.Context, in *graphopspb.HealthCheckRequest, opts ...grpc.CallOption) (*graphopspb.HealthCheckResponse, error) {
	if m.HealthCheckFunc != nil {
		return m.HealthCheckFunc(ctx, in, opts...)
	}
	return nil, nil
}

func (m *MockGraphOpsClient) GetGraphStats(ctx context.Context, in *graphopspb.GetGraphStatsRequest, opts ...grpc.CallOption) (*graphopspb.GetGraphStatsResponse, error) {
	if m.GetGraphStatsFunc != nil {
		return m.GetGraphStatsFunc(ctx, in, opts...)
	}
	return nil, nil
}

func TestGraphQueryHandlerStringValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := &MockGraphOpsClient{}

	// Create response with StringValue
	stringValue := &graphopspb.QueryValue{
		Value: &graphopspb.QueryValue_StringValue{StringValue: "test string"},
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{
					{Name: "name", Type: "STRING"},
				},
				Rows: []*graphopspb.QueryRow{
					{
						Values: []*graphopspb.QueryValue{stringValue},
					},
				},
			},
		},
		Status: "success",
		Metadata: &graphopspb.QueryMetadata{
			RowsAffected:    1,
			ExecutionTimeMs: 10,
		},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{
		GraphOpsClient: mockClient,
	}

	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n.name as name",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rec.Code)
	}

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if len(response.Results) == 0 {
		t.Error("Expected results")
	}
	if len(response.Results[0].Rows) == 0 {
		t.Error("Expected rows")
	}
	if response.Results[0].Rows[0].Values[0] != "test string" {
		t.Errorf("Expected string value 'test string', got %v", response.Results[0].Rows[0].Values[0])
	}
}

func TestGraphQueryHandlerIntValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	intValue := &graphopspb.QueryValue{
		Value: &graphopspb.QueryValue_IntValue{IntValue: 42},
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "age", Type: "INTEGER"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{intValue}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 1},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.age"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if val, ok := response.Results[0].Rows[0].Values[0].(float64); !ok || int64(val) != 42 {
		t.Errorf("Expected int value 42, got %v", response.Results[0].Rows[0].Values[0])
	}
}

func TestGraphQueryHandlerDoubleValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	doubleValue := &graphopspb.QueryValue{
		Value: &graphopspb.QueryValue_DoubleValue{DoubleValue: 3.14159},
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "score", Type: "DOUBLE"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{doubleValue}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 1},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.score"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if val, ok := response.Results[0].Rows[0].Values[0].(float64); !ok || val != 3.14159 {
		t.Errorf("Expected double value 3.14159, got %v", response.Results[0].Rows[0].Values[0])
	}
}

func TestGraphQueryHandlerBoolValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	boolValue := &graphopspb.QueryValue{
		Value: &graphopspb.QueryValue_BoolValue{BoolValue: true},
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "active", Type: "BOOLEAN"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{boolValue}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 1},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.active"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if val, ok := response.Results[0].Rows[0].Values[0].(bool); !ok || !val {
		t.Errorf("Expected bool value true, got %v", response.Results[0].Rows[0].Values[0])
	}
}

func TestGraphQueryHandlerJsonValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	jsonValue := &graphopspb.QueryValue{
		Value: &graphopspb.QueryValue_JsonValue{JsonValue: []byte(`{"key": "value"}`)},
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "metadata", Type: "JSON"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{jsonValue}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 1},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.metadata"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// JsonValue should be converted to json.RawMessage, but JSON encoding converts it to map
	// Check if it's either json.RawMessage or a map (after JSON encoding)
	val := response.Results[0].Rows[0].Values[0]
	if rawMsg, ok := val.(json.RawMessage); ok {
		if string(rawMsg) != `{"key": "value"}` {
			t.Errorf("Expected JSON value {\"key\": \"value\"}, got %s", string(rawMsg))
		}
	} else if mapVal, ok := val.(map[string]interface{}); ok {
		// After JSON encoding, RawMessage becomes a map
		if mapVal["key"] != "value" {
			t.Errorf("Expected map with key='value', got %v", mapVal)
		}
	} else {
		t.Errorf("Expected json.RawMessage or map, got %T: %v", val, val)
	}
}

func TestGraphQueryHandlerNilValueConversion(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	// Create value with nil (default case)
	nilValue := &graphopspb.QueryValue{
		Value: nil, // No value set - should default to nil
	}

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "nullable", Type: "NULL"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{nilValue}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 1},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.nullable"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Nil value should be converted to nil
	if response.Results[0].Rows[0].Values[0] != nil {
		t.Errorf("Expected nil value, got %v", response.Results[0].Rows[0].Values[0])
	}
}

func TestGraphQueryHandlerMultipleValueTypes(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	// Mix of all value types in one row
	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{
					{Name: "name", Type: "STRING"},
					{Name: "age", Type: "INTEGER"},
					{Name: "score", Type: "DOUBLE"},
					{Name: "active", Type: "BOOLEAN"},
					{Name: "metadata", Type: "JSON"},
				},
				Rows: []*graphopspb.QueryRow{
					{
						Values: []*graphopspb.QueryValue{
							{Value: &graphopspb.QueryValue_StringValue{StringValue: "John"}},
							{Value: &graphopspb.QueryValue_IntValue{IntValue: 30}},
							{Value: &graphopspb.QueryValue_DoubleValue{DoubleValue: 0.95}},
							{Value: &graphopspb.QueryValue_BoolValue{BoolValue: true}},
							{Value: &graphopspb.QueryValue_JsonValue{JsonValue: []byte(`{"key": "value"}`)}},
						},
					},
				},
			},
		},
		Status: "success",
		Metadata: &graphopspb.QueryMetadata{
			RowsAffected:    1,
			ExecutionTimeMs: 15,
			QueryPlan:       "EXPLAIN PLAN",
			Warnings:        []string{"Warning 1", "Warning 2"},
		},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.name, n.age, n.score, n.active, n.metadata"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rec.Code)
	}

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify metadata conversion
	if response.Metadata.RowsAffected != 1 {
		t.Errorf("Expected RowsAffected 1, got %d", response.Metadata.RowsAffected)
	}
	if response.Metadata.ExecutionTimeMs != 15 {
		t.Errorf("Expected ExecutionTimeMs 15, got %d", response.Metadata.ExecutionTimeMs)
	}
	if response.Metadata.QueryPlan != "EXPLAIN PLAN" {
		t.Errorf("Expected QueryPlan 'EXPLAIN PLAN', got %s", response.Metadata.QueryPlan)
	}
	if len(response.Metadata.Warnings) != 2 {
		t.Errorf("Expected 2 warnings, got %d", len(response.Metadata.Warnings))
	}
}

func TestGraphQueryHandlerEmptyResultsMocked(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "name", Type: "STRING"}},
				Rows:    []*graphopspb.QueryRow{}, // Empty rows
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 0},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) WHERE n.id = 'nonexistent' RETURN n"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if len(response.Results[0].Rows) != 0 {
		t.Errorf("Expected 0 rows, got %d", len(response.Results[0].Rows))
	}
}

func TestGraphQueryHandlerMultipleResultsMocked(t *testing.T) {
	gateway := NewGateway()
	mockClient := new(MockGraphOpsClient)

	mockResponse := &graphopspb.ExecuteQueryResponse{
		Results: []*graphopspb.QueryResult{
			{
				Columns: []*graphopspb.QueryColumn{{Name: "id", Type: "STRING"}},
				Rows: []*graphopspb.QueryRow{
					{Values: []*graphopspb.QueryValue{{Value: &graphopspb.QueryValue_StringValue{StringValue: "id1"}}}},
					{Values: []*graphopspb.QueryValue{{Value: &graphopspb.QueryValue_StringValue{StringValue: "id2"}}}},
					{Values: []*graphopspb.QueryValue{{Value: &graphopspb.QueryValue_StringValue{StringValue: "id3"}}}},
				},
			},
		},
		Status:   "success",
		Metadata: &graphopspb.QueryMetadata{RowsAffected: 3},
	}

	mockClient.ExecuteQueryFunc = func(ctx context.Context, in *graphopspb.ExecuteQueryRequest, opts ...grpc.CallOption) (*graphopspb.ExecuteQueryResponse, error) {
		return mockResponse, nil
	}

	clients := &GRPCClients{GraphOpsClient: mockClient}
	enhanced := &EnhancedGateway{Gateway: gateway, grpcClients: clients}

	body, _ := json.Marshal(map[string]interface{}{"query": "MATCH (n) RETURN n.id LIMIT 3"})
	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	var response GraphQueryResponse
	if err := json.NewDecoder(rec.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if len(response.Results[0].Rows) != 3 {
		t.Errorf("Expected 3 rows, got %d", len(response.Results[0].Rows))
	}
}
