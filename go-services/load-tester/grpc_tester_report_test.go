package main

import (
	"testing"

	"github.com/bojand/ghz/runner"
)

func TestGRPCTesterPrintReportExecution(t *testing.T) {
	config := &LoadTestConfig{
		URL: "localhost:50051",
	}
	tester := NewGRPCTester(config)
	if tester == nil {
		t.Fatal("NewGRPCTester() should not return nil")
	}

	// Create a minimal report to test printReport
	// Note: runner.Report structure may vary - use actual fields
	report := &runner.Report{
		Count:     10,
		Total:     1000000000, // 1 second
		Average:   100000000,  // 100ms average
		Fastest:   50000000,   // 50ms fastest
		Slowest:   200000000,  // 200ms slowest
		Rps:       10.0,
		ErrorDist: make(map[string]int),
		LatencyDistribution: []runner.LatencyDistribution{
			{
				Percentage: 50,
				Latency:    100000000, // 100ms p50
			},
			{
				Percentage: 95,
				Latency:    180000000, // 180ms p95
			},
			{
				Percentage: 99,
				Latency:    200000000, // 200ms p99
			},
		},
	}

	// Test that printReport doesn't panic
	tester.printReport(report)
}

func TestGRPCTesterPrintReportWithErrors(t *testing.T) {
	config := &LoadTestConfig{
		URL: "localhost:50051",
	}
	tester := NewGRPCTester(config)

	// Create report with errors
	report := &runner.Report{
		Count: 10,
		ErrorDist: map[string]int{
			"connection error": 2,
		},
	}

	// Test that printReport handles errors gracefully
	tester.printReport(report)
}

func TestGRPCTesterPrintReportEmpty(t *testing.T) {
	config := &LoadTestConfig{
		URL: "localhost:50051",
	}
	tester := NewGRPCTester(config)

	// Create minimal report
	report := &runner.Report{
		Count:               0,
		ErrorDist:           make(map[string]int),
		LatencyDistribution: []runner.LatencyDistribution{},
	}

	// Test that printReport handles empty report
	tester.printReport(report)
}
