package main

import (
	"sort"
	"time"
)

// TestResults holds all test execution results
type TestResults struct {
	StartTime          time.Time     `json:"start_time"`
	EndTime            time.Time     `json:"end_time"`
	TestDuration       time.Duration `json:"test_duration"`
	TotalRequests      int64         `json:"total_requests"`
	SuccessfulRequests int64         `json:"successful_requests"`
	FailedRequests     int64         `json:"failed_requests"`
	RequestsPerSecond  float64       `json:"requests_per_second"`
	TotalBytes         int64         `json:"total_bytes"`

	// Latency metrics
	Latencies   []time.Duration `json:"-"` // Not serialized due to size
	MinLatency  time.Duration   `json:"min_latency"`
	MaxLatency  time.Duration   `json:"max_latency"`
	MeanLatency time.Duration   `json:"mean_latency"`
	P50Latency  time.Duration   `json:"p50_latency"`
	P95Latency  time.Duration   `json:"p95_latency"`
	P99Latency  time.Duration   `json:"p99_latency"`

	// Distribution data
	StatusCodes map[int]int64    `json:"status_codes"`
	Errors      map[string]int64 `json:"errors"`

	// Performance metrics
	ConnectionErrors int64 `json:"connection_errors"`
	TimeoutErrors    int64 `json:"timeout_errors"`

	// Scenario-specific results
	ScenarioResults map[string]*ScenarioResult `json:"scenario_results,omitempty"`
}

// ScenarioResult holds results for a specific test scenario
type ScenarioResult struct {
	Name               string        `json:"name"`
	TotalRequests      int64         `json:"total_requests"`
	SuccessfulRequests int64         `json:"successful_requests"`
	FailedRequests     int64         `json:"failed_requests"`
	AverageLatency     time.Duration `json:"average_latency"`
	ErrorRate          float64       `json:"error_rate"`
}

// NewTestResults creates a new TestResults instance
func NewTestResults() *TestResults {
	return &TestResults{
		StartTime:       time.Now(),
		StatusCodes:     make(map[int]int64),
		Errors:          make(map[string]int64),
		ScenarioResults: make(map[string]*ScenarioResult),
		Latencies:       make([]time.Duration, 0, 10000), // Pre-allocate for performance
	}
}

// calculateMeanLatency calculates the mean latency from all recorded latencies
func (ht *HTTPTester) calculateMeanLatency() time.Duration {
	if len(ht.results.Latencies) == 0 {
		return 0
	}

	var total time.Duration
	for _, latency := range ht.results.Latencies {
		total += latency
	}

	return total / time.Duration(len(ht.results.Latencies))
}

// calculatePercentile calculates the specified percentile from latencies
func (ht *HTTPTester) calculatePercentile(percentile float64) time.Duration {
	if len(ht.results.Latencies) == 0 {
		return 0
	}

	// Create a sorted copy
	sorted := make([]time.Duration, len(ht.results.Latencies))
	copy(sorted, ht.results.Latencies)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i] < sorted[j]
	})

	index := int(float64(len(sorted)) * percentile / 100.0)
	if index >= len(sorted) {
		index = len(sorted) - 1
	}

	return sorted[index]
}

// Finalize completes the test results and calculates final statistics
func (tr *TestResults) Finalize() {
	tr.EndTime = time.Now()
	tr.TestDuration = tr.EndTime.Sub(tr.StartTime)

	if tr.TestDuration.Seconds() > 0 {
		tr.RequestsPerSecond = float64(tr.TotalRequests) / tr.TestDuration.Seconds()
	}

	// Calculate latency percentiles if we have data
	if len(tr.Latencies) > 0 {
		// Sort latencies for percentile calculations
		sort.Slice(tr.Latencies, func(i, j int) bool {
			return tr.Latencies[i] < tr.Latencies[j]
		})

		// Calculate percentiles
		tr.P50Latency = tr.getPercentile(50)
		tr.P95Latency = tr.getPercentile(95)
		tr.P99Latency = tr.getPercentile(99)

		// Calculate mean
		var total time.Duration
		for _, latency := range tr.Latencies {
			total += latency
		}
		tr.MeanLatency = total / time.Duration(len(tr.Latencies))
	}
}

// getPercentile calculates percentile from sorted latencies
func (tr *TestResults) getPercentile(percentile float64) time.Duration {
	if len(tr.Latencies) == 0 {
		return 0
	}

	index := int(float64(len(tr.Latencies)) * percentile / 100.0)
	if index >= len(tr.Latencies) {
		index = len(tr.Latencies) - 1
	}

	return tr.Latencies[index]
}

// GetSuccessRate returns the success rate as a percentage
func (tr *TestResults) GetSuccessRate() float64 {
	if tr.TotalRequests == 0 {
		return 0
	}
	return float64(tr.SuccessfulRequests) / float64(tr.TotalRequests) * 100
}

// GetErrorRate returns the error rate as a percentage
func (tr *TestResults) GetErrorRate() float64 {
	if tr.TotalRequests == 0 {
		return 0
	}
	return float64(tr.FailedRequests) / float64(tr.TotalRequests) * 100
}

// GetThroughputMBps returns throughput in MB/s
func (tr *TestResults) GetThroughputMBps() float64 {
	if tr.TestDuration.Seconds() == 0 {
		return 0
	}
	return float64(tr.TotalBytes) / tr.TestDuration.Seconds() / 1024 / 1024
}

// AddScenarioResult adds results for a specific scenario
func (tr *TestResults) AddScenarioResult(name string, result *ScenarioResult) {
	tr.ScenarioResults[name] = result
}

// Summary returns a brief summary of the test results
type ResultSummary struct {
	TotalRequests     int64         `json:"total_requests"`
	SuccessRate       float64       `json:"success_rate"`
	ErrorRate         float64       `json:"error_rate"`
	RequestsPerSecond float64       `json:"requests_per_second"`
	MeanLatency       time.Duration `json:"mean_latency"`
	P95Latency        time.Duration `json:"p95_latency"`
	P99Latency        time.Duration `json:"p99_latency"`
	TestDuration      time.Duration `json:"test_duration"`
	ThroughputMBps    float64       `json:"throughput_mbps"`
}

// GetSummary returns a concise summary of the test results
func (tr *TestResults) GetSummary() ResultSummary {
	return ResultSummary{
		TotalRequests:     tr.TotalRequests,
		SuccessRate:       tr.GetSuccessRate(),
		ErrorRate:         tr.GetErrorRate(),
		RequestsPerSecond: tr.RequestsPerSecond,
		MeanLatency:       tr.MeanLatency,
		P95Latency:        tr.P95Latency,
		P99Latency:        tr.P99Latency,
		TestDuration:      tr.TestDuration,
		ThroughputMBps:    tr.GetThroughputMBps(),
	}
}

// IsHealthy determines if the test results indicate a healthy system
func (tr *TestResults) IsHealthy() bool {
	successRate := tr.GetSuccessRate()
	errorRate := tr.GetErrorRate()

	// Consider healthy if:
	// - Success rate > 95%
	// - Error rate < 5%
	// - P95 latency < 1 second (for most web services)
	return successRate > 95.0 &&
		errorRate < 5.0 &&
		tr.P95Latency < time.Second
}

// GetHealthStatus returns a health status string
func (tr *TestResults) GetHealthStatus() string {
	if tr.IsHealthy() {
		return "HEALTHY"
	}

	successRate := tr.GetSuccessRate()
	if successRate < 90 {
		return "CRITICAL"
	} else if successRate < 95 {
		return "WARNING"
	}

	if tr.P95Latency > 2*time.Second {
		return "CRITICAL"
	} else if tr.P95Latency > time.Second {
		return "WARNING"
	}

	return "DEGRADED"
}
