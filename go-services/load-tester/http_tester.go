package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/fatih/color"
	"golang.org/x/time/rate"
)

// HTTPTester handles HTTP load testing
type HTTPTester struct {
	config  *LoadTestConfig
	client  *http.Client
	results *TestResults
	limiter *rate.Limiter
	mu      sync.RWMutex
}

// NewHTTPTester creates a new HTTP load tester
func NewHTTPTester(config *LoadTestConfig) *HTTPTester {
	// Configure HTTP client for high concurrency
	// Support 10,000+ concurrent connections
	maxConns := config.Concurrency * 2
	if maxConns < 20000 {
		maxConns = 20000 // Minimum pool size for 10k+ concurrency
	}
	maxConnsPerHost := config.Concurrency
	if maxConnsPerHost < 10000 {
		maxConnsPerHost = 10000 // Minimum per-host pool for 10k+ concurrency
	}

	transport := &http.Transport{
		MaxIdleConns:        maxConns,
		MaxIdleConnsPerHost: maxConnsPerHost,
		IdleConnTimeout:     90 * time.Second,
		DisableKeepAlives:   !config.KeepAlive,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: config.InsecureTLS,
		},
	}

	if !config.HTTP2 {
		transport.TLSNextProto = make(map[string]func(authority string, c *tls.Conn) http.RoundTripper)
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   config.Timeout,
	}

	// Setup rate limiter
	var limiter *rate.Limiter
	if config.RateLimit > 0 {
		limiter = rate.NewLimiter(rate.Limit(config.RateLimit), config.RateLimit)
	}

	return &HTTPTester{
		config:  config,
		client:  client,
		results: NewTestResults(),
		limiter: limiter,
	}
}

// Run executes the HTTP load test
func (ht *HTTPTester) Run(ctx context.Context) error {
	color.Cyan("🚀 Starting HTTP Load Test")
	color.White("Target: %s", ht.config.URL)
	color.White("Method: %s", ht.config.Method)
	color.White("Concurrency: %d", ht.config.Concurrency)
	color.White("Total Requests: %d", ht.config.TotalRequests)
	color.White("Duration: %v", ht.config.Duration)

	if ht.config.RateLimit > 0 {
		color.White("Rate Limit: %d req/sec", ht.config.RateLimit)
	}

	fmt.Println()

	// Start metrics collection
	go ht.collectMetrics(ctx)

	// Start real-time reporting
	go ht.reportProgress(ctx)

	// Create worker channels
	workChan := make(chan struct{}, ht.config.TotalRequests)

	// Fill work channel
	if ht.config.TotalRequests > 0 {
		for i := 0; i < ht.config.TotalRequests; i++ {
			workChan <- struct{}{}
		}
		close(workChan)
	}

	// Start workers
	var wg sync.WaitGroup

	// Ramp up workers gradually
	rampUpInterval := ht.config.RampUp / time.Duration(ht.config.Concurrency)

	for i := 0; i < ht.config.Concurrency; i++ {
		wg.Add(1)

		go func(workerID int) {
			defer wg.Done()
			ht.worker(ctx, workerID, workChan)
		}(i)

		// Gradual ramp up
		if rampUpInterval > 0 {
			select {
			case <-ctx.Done():
				break
			case <-time.After(rampUpInterval):
			}
		}
	}

	// Wait for completion or timeout
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		color.Green("✅ All workers completed")
	case <-time.After(ht.config.Duration):
		color.Yellow("⏰ Duration timeout reached")
	case <-ctx.Done():
		color.Yellow("🛑 Test cancelled")
	}

	// Ramp down period
	if ht.config.RampDown > 0 {
		color.White("⬇️  Ramping down for %v", ht.config.RampDown)
		time.Sleep(ht.config.RampDown)
	}

	// Final report
	ht.printFinalReport()

	return nil
}

// worker performs HTTP requests
func (ht *HTTPTester) worker(ctx context.Context, workerID int, workChan <-chan struct{}) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-workChan:
			ht.executeRequest(ctx, workerID)
		default:
			// No more work and not using duration-based testing
			if ht.config.TotalRequests > 0 {
				return
			}
			// For duration-based testing, continue until context is done
			if ht.config.Duration > 0 {
				ht.executeRequest(ctx, workerID)

				// Think time between requests
				if ht.config.ThinkTime > 0 {
					select {
					case <-ctx.Done():
						return
					case <-time.After(ht.config.ThinkTime):
					}
				}
			} else {
				return
			}
		}
	}
}

// executeRequest performs a single HTTP request
func (ht *HTTPTester) executeRequest(ctx context.Context, workerID int) {
	// Rate limiting
	if ht.limiter != nil {
		if err := ht.limiter.Wait(ctx); err != nil {
			return
		}
	}

	start := time.Now()

	// Create request
	var body io.Reader
	if ht.config.Body != "" {
		body = bytes.NewBufferString(ht.config.Body)
	}

	req, err := http.NewRequestWithContext(ctx, ht.config.Method, ht.config.URL, body)
	if err != nil {
		ht.recordError(err, time.Since(start))
		return
	}

	// Set headers
	if ht.config.ContentType != "" {
		req.Header.Set("Content-Type", ht.config.ContentType)
	}

	for _, header := range ht.config.Headers {
		// Parse header format: "Key: Value"
		parts := bytes.SplitN([]byte(header), []byte(":"), 2)
		if len(parts) == 2 {
			key := string(bytes.TrimSpace(parts[0]))
			value := string(bytes.TrimSpace(parts[1]))
			req.Header.Set(key, value)
		}
	}

	// Execute request
	resp, err := ht.client.Do(req)
	duration := time.Since(start)

	if err != nil {
		ht.recordError(err, duration)
		return
	}
	defer func() {
		if err := resp.Body.Close(); err != nil {
			fmt.Printf("⚠️ Failed to close response body: %v\n", err)
		}
	}()

	// Read response body
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		ht.recordError(err, duration)
		return
	}

	// Record result
	ht.recordResult(resp.StatusCode, duration, len(responseBody))

	if ht.config.Verbose {
		color.Blue("Worker %d: %s %s -> %d (%v)", workerID, ht.config.Method, ht.config.URL, resp.StatusCode, duration)
	}
}

// recordResult records a successful request result
func (ht *HTTPTester) recordResult(statusCode int, duration time.Duration, bodySize int) {
	ht.mu.Lock()
	defer ht.mu.Unlock()

	atomic.AddInt64(&ht.results.TotalRequests, 1)
	atomic.AddInt64(&ht.results.TotalBytes, int64(bodySize))

	if statusCode >= 200 && statusCode < 300 {
		atomic.AddInt64(&ht.results.SuccessfulRequests, 1)
	} else if statusCode >= 400 {
		atomic.AddInt64(&ht.results.FailedRequests, 1)
	}

	// Update latency statistics
	ht.results.Latencies = append(ht.results.Latencies, duration)

	if ht.results.MinLatency == 0 || duration < ht.results.MinLatency {
		ht.results.MinLatency = duration
	}
	if duration > ht.results.MaxLatency {
		ht.results.MaxLatency = duration
	}

	// Update status code distribution
	if ht.results.StatusCodes == nil {
		ht.results.StatusCodes = make(map[int]int64)
	}
	ht.results.StatusCodes[statusCode]++
}

// recordError records a failed request
func (ht *HTTPTester) recordError(err error, duration time.Duration) {
	ht.mu.Lock()
	defer ht.mu.Unlock()

	atomic.AddInt64(&ht.results.TotalRequests, 1)
	atomic.AddInt64(&ht.results.FailedRequests, 1)

	if ht.results.Errors == nil {
		ht.results.Errors = make(map[string]int64)
	}
	ht.results.Errors[err.Error()]++

	if ht.config.Verbose {
		color.Red("❌ Error: %v (duration: %v)", err, duration)
	}
}

// collectMetrics collects real-time metrics
func (ht *HTTPTester) collectMetrics(ctx context.Context) {
	// Ensure ReportInterval is valid before creating ticker
	interval := ht.config.ReportInterval
	if interval <= 0 {
		interval = 1 * time.Second // Default to 1 second if not set
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// Update metrics
			ht.mu.RLock()
			ht.results.TestDuration = time.Since(ht.results.StartTime)

			if ht.results.TotalRequests > 0 {
				ht.results.RequestsPerSecond = float64(ht.results.TotalRequests) / ht.results.TestDuration.Seconds()
			}
			ht.mu.RUnlock()
		}
	}
}

// reportProgress reports real-time progress
func (ht *HTTPTester) reportProgress(ctx context.Context) {
	// Ensure ReportInterval is valid before creating ticker
	interval := ht.config.ReportInterval
	if interval <= 0 {
		interval = 1 * time.Second // Default to 1 second if not set
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	lastTotal := int64(0)

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			current := atomic.LoadInt64(&ht.results.TotalRequests)
			successful := atomic.LoadInt64(&ht.results.SuccessfulRequests)
			failed := atomic.LoadInt64(&ht.results.FailedRequests)

			rps := float64(current-lastTotal) / ht.config.ReportInterval.Seconds()
			successRate := float64(successful) / float64(current) * 100

			color.White("📊 Requests: %d | Success: %d (%.1f%%) | Failed: %d | RPS: %.1f",
				current, successful, successRate, failed, rps)

			lastTotal = current
		}
	}
}

// printFinalReport prints the final test results
func (ht *HTTPTester) printFinalReport() {
	color.Cyan("\n📈 Final Test Results")
	color.White("=" + string(bytes.Repeat([]byte("="), 50)))

	// Basic statistics
	total := atomic.LoadInt64(&ht.results.TotalRequests)
	successful := atomic.LoadInt64(&ht.results.SuccessfulRequests)
	failed := atomic.LoadInt64(&ht.results.FailedRequests)
	duration := time.Since(ht.results.StartTime)

	color.White("Total Requests:      %d", total)
	color.Green("Successful:          %d (%.1f%%)", successful, float64(successful)/float64(total)*100)
	if failed > 0 {
		color.Red("Failed:              %d (%.1f%%)", failed, float64(failed)/float64(total)*100)
	}
	color.White("Test Duration:       %v", duration)
	color.White("Requests/sec:        %.2f", float64(total)/duration.Seconds())

	// Latency statistics
	if len(ht.results.Latencies) > 0 {
		color.Cyan("\n⏱️  Latency Statistics")
		color.White("Min:                 %v", ht.results.MinLatency)
		color.White("Max:                 %v", ht.results.MaxLatency)
		color.White("Mean:                %v", ht.calculateMeanLatency())
		color.White("50th percentile:    %v", ht.calculatePercentile(50))
		color.White("95th percentile:     %v", ht.calculatePercentile(95))
		color.White("99th percentile:     %v", ht.calculatePercentile(99))
	}

	// Status code distribution
	if len(ht.results.StatusCodes) > 0 {
		color.Cyan("\n📋 Status Code Distribution")
		for code, count := range ht.results.StatusCodes {
			percentage := float64(count) / float64(total) * 100
			if code >= 200 && code < 300 {
				color.Green("%d: %d (%.1f%%)", code, count, percentage)
			} else if code >= 400 {
				color.Red("%d: %d (%.1f%%)", code, count, percentage)
			} else {
				color.White("%d: %d (%.1f%%)", code, count, percentage)
			}
		}
	}

	// Error summary
	if len(ht.results.Errors) > 0 {
		color.Red("\n❌ Error Summary")
		for err, count := range ht.results.Errors {
			color.Red("%s: %d", err, count)
		}
	}

	// Bandwidth
	totalBytes := atomic.LoadInt64(&ht.results.TotalBytes)
	if totalBytes > 0 {
		color.Cyan("\n📶 Bandwidth")
		mbps := float64(totalBytes) / duration.Seconds() / 1024 / 1024
		color.White("Total Bytes:         %d", totalBytes)
		color.White("Throughput:          %.2f MB/s", mbps)
	}

	color.White("\n" + string(bytes.Repeat([]byte("="), 60)))
}
