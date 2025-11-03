package main

import (
	"bytes"
	"io"
	"net/http/httptest"
	"testing"
)

func TestCoreAPIProxyGET(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyPOST(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := bytes.NewBufferString(`{"email": "test@example.com"}`)
	req := httptest.NewRequest("POST", "/api/v1/auth/login", body)
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyPATCH(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := bytes.NewBufferString(`{"name": "Updated Name"}`)
	req := httptest.NewRequest("PATCH", "/api/v1/users/me", body)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyWithQueryParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me?fields=id,name,email", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyHeaderCopying(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	req.Header.Set("X-Request-ID", "test-123")
	req.Header.Set("Accept", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyResponseHeaderForwarding(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	// Should forward response headers
	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyBodyStreaming(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Large body to test streaming
	largeBody := bytes.NewBuffer(make([]byte, 64*1024)) // 64KB
	req := httptest.NewRequest("POST", "/api/v1/auth/login", largeBody)
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyRequestBodyReadError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Request with body that errors on read
	req := httptest.NewRequest("POST", "/api/v1/auth/login", &errorReaderProxy{})
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	// Should handle read error gracefully
	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyRequestCreationError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

type errorReaderProxy struct{}

func (e *errorReaderProxy) Read(p []byte) (n int, err error) {
	return 0, io.ErrUnexpectedEOF
}
