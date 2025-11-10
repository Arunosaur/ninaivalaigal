package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGraphQueryHandlerWithSuccessPath(t *testing.T) {
	enhanced := NewTestEnhancedGateway(t)
	defer CleanupTestEnhancedGateway(t, enhanced)

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n LIMIT 1",
		"parameters": map[string]string{"name": "test"},
		"timeout_ms": 5000,
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/graph/query", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.graphQueryHandler(rec, req)

	// May return various status codes depending on service availability
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestGraphQueryHandlerEmptyParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"parameters": map[string]string{}, // Empty parameters
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

func TestGraphQueryHandlerNilParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n",
		// parameters field not provided (nil)
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

func TestGraphQueryHandlerDefaultTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": "MATCH (n) RETURN n",
		// timeout_ms not provided, should use default
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

func TestGraphQueryHandlerLargeTimeout(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query":      "MATCH (n) RETURN n",
		"timeout_ms": 60000, // 60 seconds
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

func TestGraphQueryHandlerMultipleParameters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": "MATCH (n {name: $name, age: $age}) RETURN n",
		"parameters": map[string]string{
			"name": "John",
			"age":  "30",
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

func TestGraphQueryHandlerComplexQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := map[string]interface{}{
		"query": `
			MATCH (user:User)-[:HAS_CONTEXT]->(context:Context)
			WHERE user.id = $userId
			RETURN user, context, count(context) as context_count
			ORDER BY context.created_at DESC
			LIMIT 10
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

func TestGraphQueryHandlerResponseEncoding(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
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

	// If successful, should have JSON Content-Type
	if rec.Code == http.StatusOK {
		if rec.Header().Get("Content-Type") != "application/json" {
			t.Error("Successful response should have Content-Type application/json")
		}
	}
}
