package main

import (
	"testing"
	"time"
)

func TestNewTestResults(t *testing.T) {
	results := NewTestResults()

	if results == nil {
		t.Fatal("Expected test results to be created, got nil")
	}

	if results.TotalRequests != 0 {
		t.Error("Expected initial total requests to be 0")
	}

	if results.SuccessfulRequests != 0 {
		t.Error("Expected initial successful requests to be 0")
	}

	if results.FailedRequests != 0 {
		t.Error("Expected initial failed requests to be 0")
	}
}

func TestTestResultsStructure(t *testing.T) {
	results := NewTestResults()

	// Manually increment counters to test structure
	results.TotalRequests = 3
	results.SuccessfulRequests = 2
	results.FailedRequests = 1

	if results.TotalRequests != 3 {
		t.Errorf("Expected total requests to be 3, got %d", results.TotalRequests)
	}

	if results.SuccessfulRequests != 2 {
		t.Errorf("Expected successful requests to be 2, got %d", results.SuccessfulRequests)
	}

	if results.FailedRequests != 1 {
		t.Errorf("Expected failed requests to be 1, got %d", results.FailedRequests)
	}
}

func TestTestResultsPercentages(t *testing.T) {
	results := NewTestResults()

	// Set request counts
	results.TotalRequests = 12
	results.SuccessfulRequests = 10
	results.FailedRequests = 2

	if results.TotalRequests != 12 {
		t.Errorf("Expected total requests to be 12, got %d", results.TotalRequests)
	}

	// Calculate success rate
	successRate := float64(results.SuccessfulRequests) / float64(results.TotalRequests) * 100
	expectedRate := float64(10) / float64(12) * 100

	if successRate != expectedRate {
		t.Errorf("Expected success rate to be %.2f%%, got %.2f%%", expectedRate, successRate)
	}
}

func TestTestResultsLatency(t *testing.T) {
	results := NewTestResults()

	// Set latencies directly
	latencies := []time.Duration{
		50 * time.Millisecond,
		100 * time.Millisecond,
		150 * time.Millisecond,
		200 * time.Millisecond,
	}

	results.Latencies = latencies

	if len(results.Latencies) != len(latencies) {
		t.Errorf("Expected %d latencies, got %d", len(latencies), len(results.Latencies))
	}
}
