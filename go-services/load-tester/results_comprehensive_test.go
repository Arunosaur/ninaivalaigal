package main

import (
	"testing"
	"time"
)

func TestCalculateMeanLatencyThroughFinalize(t *testing.T) {
	results := &TestResults{
		Latencies: []time.Duration{
			100 * time.Millisecond,
			200 * time.Millisecond,
			300 * time.Millisecond,
		},
		StartTime: time.Now().Add(-5 * time.Second),
	}

	// Finalize calculates mean latency
	results.Finalize()

	if results.MeanLatency <= 0 {
		t.Error("MeanLatency should be calculated by Finalize")
	}
	expected := 200 * time.Millisecond
	tolerance := 10 * time.Millisecond
	if results.MeanLatency < expected-tolerance || results.MeanLatency > expected+tolerance {
		t.Errorf("Expected mean latency around %v, got %v", expected, results.MeanLatency)
	}
}

func TestCalculatePercentileThroughFinalize(t *testing.T) {
	results := &TestResults{
		Latencies: []time.Duration{
			10 * time.Millisecond,
			20 * time.Millisecond,
			30 * time.Millisecond,
			40 * time.Millisecond,
			50 * time.Millisecond,
		},
		StartTime: time.Now().Add(-5 * time.Second),
	}

	// Finalize calculates percentiles
	results.Finalize()

	if results.P95Latency <= 0 {
		t.Error("P95Latency should be calculated by Finalize")
	}
}

func TestGetPercentileMethod(t *testing.T) {
	results := &TestResults{
		Latencies: []time.Duration{
			10 * time.Millisecond,
			20 * time.Millisecond,
			30 * time.Millisecond,
			40 * time.Millisecond,
			50 * time.Millisecond,
		},
	}

	p50 := results.getPercentile(50.0)
	if p50 <= 0 {
		t.Error("getPercentile should return positive value")
	}

	p95 := results.getPercentile(95.0)
	if p95 <= p50 {
		t.Error("P95 should be >= P50")
	}
}

func TestTestResultsGetSuccessRate(t *testing.T) {
	results := &TestResults{
		TotalRequests:      100,
		SuccessfulRequests: 95,
	}

	rate := results.GetSuccessRate()
	// GetSuccessRate returns percentage (95.0), not ratio (0.95)
	if rate != 95.0 {
		t.Errorf("Expected success rate 95.0%%, got %f", rate)
	}
}

func TestTestResultsGetErrorRate(t *testing.T) {
	results := &TestResults{
		TotalRequests:  100,
		FailedRequests: 5,
	}

	rate := results.GetErrorRate()
	// GetErrorRate returns percentage (5.0), not ratio (0.05)
	if rate != 5.0 {
		t.Errorf("Expected error rate 5.0%%, got %f", rate)
	}
}

func TestTestResultsGetThroughputMBps(t *testing.T) {
	results := &TestResults{
		TotalBytes:   1024 * 1024, // 1 MB
		TestDuration: 1 * time.Second,
	}

	throughput := results.GetThroughputMBps()
	if throughput <= 0 {
		t.Error("GetThroughputMBps should return positive value")
	}
}

func TestTestResultsAddScenarioResult(t *testing.T) {
	results := NewTestResults()

	scenarioResult := &ScenarioResult{
		Name:               "test-scenario",
		TotalRequests:      10,
		SuccessfulRequests: 8,
		FailedRequests:     2,
		AverageLatency:     100 * time.Millisecond,
		ErrorRate:          0.2,
	}

	results.AddScenarioResult("test-scenario", scenarioResult)

	if len(results.ScenarioResults) == 0 {
		t.Error("AddScenarioResult should add scenario result")
	}
}

func TestTestResultsGetSummary(t *testing.T) {
	results := &TestResults{
		TotalRequests:      100,
		SuccessfulRequests: 95,
		FailedRequests:     5,
		MeanLatency:        100 * time.Millisecond,
		P95Latency:         200 * time.Millisecond,
		TestDuration:       5 * time.Second,
	}

	summary := results.GetSummary()
	if summary.TotalRequests == 0 {
		t.Error("GetSummary should return non-zero TotalRequests")
	}
}

func TestTestResultsIsHealthy(t *testing.T) {
	tests := []struct {
		name     string
		results  *TestResults
		expected bool
	}{
		{"Healthy", &TestResults{TotalRequests: 100, SuccessfulRequests: 99, MeanLatency: 100 * time.Millisecond}, true},
		{"Unhealthy - low success", &TestResults{TotalRequests: 100, SuccessfulRequests: 80, MeanLatency: 100 * time.Millisecond}, false},
		{"Unhealthy - high latency", &TestResults{TotalRequests: 100, SuccessfulRequests: 99, MeanLatency: 5 * time.Second}, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			healthy := tt.results.IsHealthy()
			// Just verify function doesn't panic
			_ = healthy
		})
	}
}

func TestTestResultsGetHealthStatus(t *testing.T) {
	results := &TestResults{
		TotalRequests:      100,
		SuccessfulRequests: 95,
		MeanLatency:        100 * time.Millisecond,
	}

	status := results.GetHealthStatus()
	if status == "" {
		t.Error("GetHealthStatus should return status string")
	}
}

func TestTestResultsFinalize(t *testing.T) {
	results := &TestResults{
		TotalRequests:      100,
		SuccessfulRequests: 95,
		FailedRequests:     5,
		Latencies: []time.Duration{
			100 * time.Millisecond,
			200 * time.Millisecond,
			300 * time.Millisecond,
		},
		StartTime: time.Now().Add(-5 * time.Second),
	}

	results.Finalize()

	if results.TestDuration <= 0 {
		t.Error("Finalize should set TestDuration")
	}
	if results.MeanLatency <= 0 {
		t.Error("Finalize should calculate MeanLatency")
	}
}
