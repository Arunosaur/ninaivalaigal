package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/bojand/ghz/runner"
	"github.com/fatih/color"
)

// GRPCTester handles gRPC load testing using the ghz runner under the hood.
type GRPCTester struct {
	config *LoadTestConfig
}

// NewGRPCTester creates a new gRPC load tester instance.
func NewGRPCTester(cfg *LoadTestConfig) *GRPCTester {
	return &GRPCTester{config: cfg}
}

// Run executes the gRPC load test.
func (gt *GRPCTester) Run(ctx context.Context) error {
	call, err := gt.resolveCall()
	if err != nil {
		return err
	}

	color.Cyan("🚀 Starting gRPC Load Test")
	color.White("Target: %s", gt.config.URL)
	color.White("Call:   %s", call)
	color.White("Concurrency: %d", gt.config.Concurrency)

	if gt.config.TotalRequests > 0 {
		color.White("Total Requests: %d", gt.config.TotalRequests)
	} else {
		color.White("Duration: %v", gt.config.Duration)
	}

	if gt.config.RateLimit > 0 {
		color.White("RPS Limit: %d", gt.config.RateLimit)
	}

	if gt.config.ProtoFile != "" {
		color.White("Proto File: %s", gt.config.ProtoFile)
	} else {
		color.White("Reflection: enabled (no proto supplied)")
	}

	fmt.Println()

	options, err := gt.buildOptions()
	if err != nil {
		return err
	}

	reportCh := make(chan *runner.Report, 1)
	errCh := make(chan error, 1)

	go func() {
		report, runErr := runner.Run(call, gt.config.URL, options...)
		if runErr != nil {
			errCh <- runErr
			return
		}
		reportCh <- report
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case runErr := <-errCh:
		return runErr
	case report := <-reportCh:
		gt.printReport(report)
	}

	return nil
}

func (gt *GRPCTester) resolveCall() (string, error) {
	method := strings.TrimSpace(gt.config.GRPCMethod)
	service := strings.TrimSpace(gt.config.GRPCService)

	if method == "" {
		return "", fmt.Errorf("gRPC method is required (use --method or provide service/method)")
	}

	if strings.Contains(method, "/") {
		return method, nil
	}

	if service == "" {
		return "", fmt.Errorf("gRPC service is required when method does not include the service name")
	}

	return fmt.Sprintf("%s/%s", service, method), nil
}

func (gt *GRPCTester) buildOptions() ([]runner.Option, error) {
	options := []runner.Option{
		runner.WithConcurrency(uint(gt.config.Concurrency)),
		runner.WithTimeout(gt.config.Timeout),
		runner.WithInsecure(gt.config.GRPCPlaintext),
	}

	if gt.config.TotalRequests > 0 {
		options = append(options, runner.WithTotalRequests(uint(gt.config.TotalRequests)))
	} else {
		if gt.config.Duration <= 0 {
			return nil, fmt.Errorf("duration must be greater than zero when total requests is not specified")
		}
		options = append(options, runner.WithRunDuration(gt.config.Duration))
	}

	if gt.config.RateLimit > 0 {
		options = append(options, runner.WithRPS(uint(gt.config.RateLimit)))
	}

	if gt.config.ProtoFile != "" {
		protoDir := filepath.Dir(gt.config.ProtoFile)
		options = append(options, runner.WithProtoFile(gt.config.ProtoFile, []string{protoDir}))
	}

	payload := gt.config.Body
	if payload == "" && gt.config.BodyFile != "" {
		data, err := os.ReadFile(gt.config.BodyFile)
		if err != nil {
			return nil, fmt.Errorf("failed to read data file: %w", err)
		}
		payload = string(data)
	}

	if payload != "" {
		options = append(options, runner.WithDataFromJSON(payload))
	}

	if len(gt.config.Headers) > 0 {
		metadata := make(map[string]string, len(gt.config.Headers))
		for _, header := range gt.config.Headers {
			parts := strings.SplitN(header, ":", 2)
			if len(parts) != 2 {
				return nil, fmt.Errorf("invalid header format: %q (expected 'Key: Value')", header)
			}

			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			metadata[key] = value
		}

		options = append(options, runner.WithMetadata(metadata))
	}

	return options, nil
}

func (gt *GRPCTester) printReport(report *runner.Report) {
	failures := 0
	for _, count := range report.ErrorDist {
		failures += count
	}

	successful := int(report.Count) - failures
	successRate := 0.0
	errorRate := 0.0

	if report.Count > 0 {
		successRate = float64(successful) / float64(report.Count) * 100.0
		errorRate = float64(failures) / float64(report.Count) * 100.0
	}

	color.Cyan("📈 Final gRPC Test Results")
	color.White("Total Requests:      %d", report.Count)
	color.Green("Successful:          %d (%.2f%%)", successful, successRate)
	if failures > 0 {
		color.Red("Failed:              %d (%.2f%%)", failures, errorRate)
	}
	color.White("Test Duration:       %v", report.Total)
	color.White("Requests/sec:        %.2f", report.Rps)
	color.White("Average Latency:     %v", report.Average)
	color.White("Fastest:             %v", report.Fastest)
	color.White("Slowest:             %v", report.Slowest)

	percentiles := map[int]time.Duration{}
	for _, dist := range report.LatencyDistribution {
		percentiles[dist.Percentage] = dist.Latency
	}

	if len(percentiles) > 0 {
		color.Cyan("\n⏱️  Latency Percentiles")
		if p50, ok := percentiles[50]; ok {
			color.White("P50:                %v", p50)
		}
		if p95, ok := percentiles[95]; ok {
			color.White("P95:                %v", p95)
		}
		if p99, ok := percentiles[99]; ok {
			color.White("P99:                %v", p99)
		}
	}

	if len(report.StatusCodeDist) > 0 {
		color.Cyan("\n📋 gRPC Status Distribution")
		for code, count := range report.StatusCodeDist {
			percentage := float64(count) / float64(report.Count) * 100.0

			if statusNumeric, err := strconv.Atoi(code); err == nil {
				if statusNumeric == 0 {
					color.Green("%s: %d (%.2f%%)", code, count, percentage)
				} else {
					color.Yellow("%s: %d (%.2f%%)", code, count, percentage)
				}
			} else {
				// Non-numeric codes (e.g., OK, UNKNOWN)
				if strings.EqualFold(code, "OK") {
					color.Green("%s: %d (%.2f%%)", code, count, percentage)
				} else {
					color.Red("%s: %d (%.2f%%)", code, count, percentage)
				}
			}
		}
	}

	if len(report.ErrorDist) > 0 {
		color.Red("\n❌ Error Distribution")
		for errMsg, count := range report.ErrorDist {
			color.Red("%s: %d", errMsg, count)
		}
	}

	color.White("\n" + strings.Repeat("=", 60))
}
