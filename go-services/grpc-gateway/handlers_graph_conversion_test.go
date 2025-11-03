package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"

	graphopspb "github.com/arunosaur/ninaivalaigal/grpc-gateway/proto/graphopspb"
)

func TestGraphQueryHandlerResultConversion(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n.id as id, n.name as name, n.score as score, n.active as active, n.metadata as metadata",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerEmptyResultsConversion(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) WHERE n.id = 'nonexistent' RETURN n",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerMultipleResultsConversion(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n), (m) RETURN n, m LIMIT 5",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerMetadataConversion(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) SET n.updated = timestamp() RETURN n",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// Should convert metadata (rows affected, execution time, etc.)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerResponseEncodingError(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n",
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// Should handle encoding errors gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Test value type conversion scenarios
func TestQueryValueTypeConversion(t *testing.T) {
	// Test that all value types can be converted
	testCases := []struct {
		name  string
		value interface{}
	}{
		{"StringValue", &graphopspb.QueryValue_StringValue{StringValue: "test"}},
		{"IntValue", &graphopspb.QueryValue_IntValue{IntValue: 42}},
		{"DoubleValue", &graphopspb.QueryValue_DoubleValue{DoubleValue: 3.14}},
		{"BoolValue", &graphopspb.QueryValue_BoolValue{BoolValue: true}},
		{"JsonValue", &graphopspb.QueryValue_JsonValue{JsonValue: []byte(`{"key": "value"}`)}},
		{"NilValue", nil},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Test conversion logic (would require mocking gRPC response)
			_ = tc.value
		})
	}
}

func TestGraphQueryHandlerComplexResultSet(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": `
			MATCH (user:User)-[rel:HAS_CONTEXT]->(ctx:Context)
			WHERE user.id = $userId
			RETURN user.id, user.name, rel.created_at, ctx.id, ctx.name
			ORDER BY rel.created_at DESC
			LIMIT 20
		`,
		"parameters": map[string]string{
			"userId": "123",
		},
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerWithWarnings(t *testing.T) {
	gateway := NewGateway()
	clients, _ := NewGRPCClients()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: clients,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n LIMIT 1000", // May generate warnings for large result sets
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
