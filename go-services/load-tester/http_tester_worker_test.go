package main

import (
	"context"
	"testing"
	"time"
)

func TestHTTPTesterWorkerWithContext(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Timeout = 100 * time.Millisecond

	tester := NewHTTPTester(config)
	if tester == nil {
		t.Fatal("NewHTTPTester should not return nil")
	}

	// Test worker with canceled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	workChan := make(chan struct{}, 1)
	workChan <- struct{}{}

	// Worker should return when context is canceled
	go func() {
		tester.worker(ctx, 1, workChan)
	}()

	// Give worker time to process
	time.Sleep(50 * time.Millisecond)
}

func TestHTTPTesterWorkerWithWorkChannel(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 1
	config.Timeout = 100 * time.Millisecond

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	workChan := make(chan struct{}, 2)
	workChan <- struct{}{}
	workChan <- struct{}{}

	// Worker should process work from channel
	go func() {
		tester.worker(ctx, 1, workChan)
	}()

	time.Sleep(100 * time.Millisecond)
}

func TestHTTPTesterWorkerWithTotalRequests(t *testing.T) {
	config := NewLoadTestConfig()
	config.URL = "http://localhost:8080/health"
	config.Concurrency = 1
	config.TotalRequests = 5
	config.Timeout = 100 * time.Millisecond

	tester := NewHTTPTester(config)

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	workChan := make(chan struct{}, 10)
	// Fill channel with work
	for i := 0; i < 5; i++ {
		workChan <- struct{}{}
	}

	// Worker should process and exit when TotalRequests is reached
	go func() {
		tester.worker(ctx, 1, workChan)
	}()

	time.Sleep(200 * time.Millisecond)
}

func TestHTTPTesterCalculateMeanLatency(t *testing.T) {
	config := NewLoadTestConfig()
	tester := NewHTTPTester(config)

	// Add some latencies
	tester.results.Latencies = []time.Duration{
		100 * time.Millisecond,
		150 * time.Millisecond,
		200 * time.Millisecond,
	}

	mean := tester.calculateMeanLatency()
	if mean == 0 {
		t.Error("Mean latency should be calculated")
	}
}

func TestHTTPTesterCalculateMeanLatencyEmpty(t *testing.T) {
	config := NewLoadTestConfig()
	tester := NewHTTPTester(config)

	tester.results.Latencies = []time.Duration{}

	mean := tester.calculateMeanLatency()
	if mean != 0 {
		t.Errorf("Expected mean latency 0 for empty latencies, got %v", mean)
	}
}

func TestHTTPTesterCalculatePercentile(t *testing.T) {
	config := NewLoadTestConfig()
	tester := NewHTTPTester(config)

	// Add latencies
	tester.results.Latencies = []time.Duration{
		100 * time.Millisecond,
		150 * time.Millisecond,
		200 * time.Millisecond,
		120 * time.Millisecond,
		180 * time.Millisecond,
	}

	p50 := tester.calculatePercentile(50)
	if p50 == 0 {
		t.Error("P50 percentile should be calculated")
	}

	p95 := tester.calculatePercentile(95)
	if p95 == 0 {
		t.Error("P95 percentile should be calculated")
	}

	p99 := tester.calculatePercentile(99)
	if p99 == 0 {
		t.Error("P99 percentile should be calculated")
	}
}

func TestHTTPTesterCalculatePercentileEmpty(t *testing.T) {
	config := NewLoadTestConfig()
	tester := NewHTTPTester(config)

	tester.results.Latencies = []time.Duration{}

	p50 := tester.calculatePercentile(50)
	if p50 != 0 {
		t.Errorf("Expected percentile 0 for empty latencies, got %v", p50)
	}
}

func TestHTTPTesterCalculatePercentileBoundary(t *testing.T) {
	config := NewLoadTestConfig()
	tester := NewHTTPTester(config)

	// Single latency
	tester.results.Latencies = []time.Duration{
		100 * time.Millisecond,
	}

	p50 := tester.calculatePercentile(50)
	if p50 == 0 {
		t.Error("P50 should be calculated even with single latency")
	}
}
