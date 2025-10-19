package main

import (
	"time"
)

// LoadTestConfig holds all configuration for load testing
type LoadTestConfig struct {
	// Global settings
	Verbose      bool   `json:"verbose"`
	OutputFormat string `json:"output_format"`
	MetricsAddr  string `json:"metrics_addr"`

	// Test parameters
	URL         string   `json:"url"`
	Method      string   `json:"method"`
	Headers     []string `json:"headers"`
	Body        string   `json:"body"`
	ContentType string   `json:"content_type"`

	// Load parameters
	Concurrency   int           `json:"concurrency"`
	TotalRequests int           `json:"total_requests"`
	Duration      time.Duration `json:"duration"`
	RateLimit     int           `json:"rate_limit"`

	// Connection settings
	Timeout     time.Duration `json:"timeout"`
	KeepAlive   bool          `json:"keep_alive"`
	HTTP2       bool          `json:"http2"`
	InsecureTLS bool          `json:"insecure_tls"`

	// Advanced patterns
	RampUp    time.Duration `json:"ramp_up"`
	RampDown  time.Duration `json:"ramp_down"`
	ThinkTime time.Duration `json:"think_time"`

	// Scenario settings
	ScenarioFile string            `json:"scenario_file"`
	Variables    map[string]string `json:"variables"`

	// Metrics settings
	ReportInterval time.Duration `json:"report_interval"`
	MetricsEnabled bool          `json:"metrics_enabled"`

	// gRPC specific
	GRPCService string `json:"grpc_service"`
	GRPCMethod  string `json:"grpc_method"`
	ProtoFile   string `json:"proto_file"`

	// WebSocket specific
	WSProtocol      string        `json:"ws_protocol"`
	WSOrigin        string        `json:"ws_origin"`
	MessageInterval time.Duration `json:"message_interval"`
}

// NewLoadTestConfig creates a new configuration with defaults
func NewLoadTestConfig() *LoadTestConfig {
	return &LoadTestConfig{
		// Defaults
		Method:          "GET",
		ContentType:     "application/json",
		Concurrency:     1,
		TotalRequests:   100,
		Duration:        30 * time.Second,
		Timeout:         30 * time.Second,
		KeepAlive:       true,
		HTTP2:           true,
		RampUp:          5 * time.Second,
		RampDown:        5 * time.Second,
		ReportInterval:  1 * time.Second,
		MetricsEnabled:  false,
		MessageInterval: 1 * time.Second,
		Variables:       make(map[string]string),
	}
}

// TestProfile defines common testing profiles
type TestProfile struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Config      LoadTestConfig `json:"config"`
}

// GetDefaultProfiles returns predefined testing profiles
func GetDefaultProfiles() []TestProfile {
	return []TestProfile{
		{
			Name:        "smoke",
			Description: "Quick smoke test with low load",
			Config: LoadTestConfig{
				Concurrency:   1,
				TotalRequests: 10,
				Duration:      10 * time.Second,
				Timeout:       5 * time.Second,
			},
		},
		{
			Name:        "load",
			Description: "Standard load test",
			Config: LoadTestConfig{
				Concurrency:   50,
				TotalRequests: 1000,
				Duration:      60 * time.Second,
				RampUp:        10 * time.Second,
				RampDown:      10 * time.Second,
			},
		},
		{
			Name:        "stress",
			Description: "High-load stress test",
			Config: LoadTestConfig{
				Concurrency:   200,
				TotalRequests: 10000,
				Duration:      300 * time.Second,
				RampUp:        30 * time.Second,
				RampDown:      30 * time.Second,
			},
		},
		{
			Name:        "spike",
			Description: "Sudden traffic spike test",
			Config: LoadTestConfig{
				Concurrency:   500,
				TotalRequests: 5000,
				Duration:      60 * time.Second,
				RampUp:        5 * time.Second,
				RampDown:      5 * time.Second,
			},
		},
		{
			Name:        "endurance",
			Description: "Long-running endurance test",
			Config: LoadTestConfig{
				Concurrency: 100,
				Duration:    1800 * time.Second, // 30 minutes
				RampUp:      60 * time.Second,
				RampDown:    60 * time.Second,
			},
		},
		{
			Name:        "grpc-gateway",
			Description: "Test gRPC Gateway performance",
			Config: LoadTestConfig{
				Concurrency:   100,
				TotalRequests: 10000,
				Duration:      120 * time.Second,
				RampUp:        15 * time.Second,
				RampDown:      15 * time.Second,
				Method:        "POST",
				ContentType:   "application/json",
			},
		},
	}
}

// TestTarget defines a target service for testing
type TestTarget struct {
	Name      string            `json:"name"`
	BaseURL   string            `json:"base_url"`
	Endpoints []TestEndpoint    `json:"endpoints"`
	Headers   map[string]string `json:"headers"`
	Timeout   time.Duration     `json:"timeout"`
}

// TestEndpoint defines an endpoint to test
type TestEndpoint struct {
	Path     string            `json:"path"`
	Method   string            `json:"method"`
	Headers  map[string]string `json:"headers"`
	Body     string            `json:"body"`
	Weight   int               `json:"weight"` // For weighted random selection
	Validate []ValidationRule  `json:"validate"`
}

// ValidationRule defines response validation
type ValidationRule struct {
	Type     string `json:"type"`     // status_code, response_time, json_path, header
	Field    string `json:"field"`    // field to validate
	Operator string `json:"operator"` // eq, ne, lt, gt, contains, exists
	Value    string `json:"value"`    // expected value
}

// GetNinaivalaigalTargets returns predefined service targets
func GetNinaivalaigalTargets() []TestTarget {
	return []TestTarget{
		{
			Name:    "grpc-gateway",
			BaseURL: "http://localhost:8080",
			Headers: map[string]string{
				"Content-Type":  "application/json",
				"Authorization": "Bearer test-token",
			},
			Timeout: 30 * time.Second,
			Endpoints: []TestEndpoint{
				{
					Path:   "/health",
					Method: "GET",
					Weight: 10,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
						{Type: "response_time", Operator: "lt", Value: "100ms"},
					},
				},
				{
					Path:   "/api/v1/memory/remember",
					Method: "POST",
					Body:   `{"content":"Load test memory","context":"performance_testing","metadata":{"test":"load"}}`,
					Weight: 30,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
						{Type: "json_path", Field: "status", Operator: "eq", Value: "success"},
					},
				},
				{
					Path:   "/api/v1/memory/recall?q=test&limit=10",
					Method: "GET",
					Weight: 25,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
						{Type: "json_path", Field: "memories", Operator: "exists", Value: ""},
					},
				},
				{
					Path:   "/api/v1/graph/query",
					Method: "POST",
					Body:   `{"query":"MATCH (n) RETURN count(n) as node_count","parameters":{},"timeout_ms":5000}`,
					Weight: 20,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
						{Type: "json_path", Field: "results", Operator: "exists", Value: ""},
					},
				},
				{
					Path:   "/api/v1/memory/memories?page=1&page_size=20",
					Method: "GET",
					Weight: 15,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
						{Type: "response_time", Operator: "lt", Value: "500ms"},
					},
				},
			},
		},
		{
			Name:    "memory-service",
			BaseURL: "http://localhost:13393",
			Headers: map[string]string{
				"Content-Type": "application/json",
			},
			Timeout: 30 * time.Second,
			Endpoints: []TestEndpoint{
				{
					Path:   "/health",
					Method: "GET",
					Weight: 100,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
					},
				},
			},
		},
		{
			Name:    "graphops-service",
			BaseURL: "http://localhost:50051",
			Headers: map[string]string{
				"Content-Type": "application/json",
			},
			Timeout: 30 * time.Second,
			Endpoints: []TestEndpoint{
				{
					Path:   "/health",
					Method: "GET",
					Weight: 100,
					Validate: []ValidationRule{
						{Type: "status_code", Operator: "eq", Value: "200"},
					},
				},
			},
		},
	}
}
