package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

// createHTTPCommand creates the HTTP load testing command
func createHTTPCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "http [URL]",
		Short: "Run HTTP load test against a target URL",
		Long: `Run HTTP load test against a target URL with configurable parameters.

Examples:
  # Basic load test
  load-tester http http://localhost:8080/health --concurrency 10 --requests 100

  # Stress test with rate limiting
  load-tester http http://localhost:8080/api/v1/memory/remember \
    --method POST \
    --body '{"content":"test","context":"load"}' \
    --concurrency 50 \
    --duration 60s \
    --rate-limit 100

  # Test with custom headers
  load-tester http http://localhost:8080/api/v1/graph/query \
    --method POST \
    --header "Authorization: Bearer token123" \
    --header "Content-Type: application/json" \
    --body '{"query":"MATCH (n) RETURN n LIMIT 1"}' \
    --concurrency 25 \
    --requests 500`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			config.URL = args[0]

			// Validate configuration
			if err := validateHTTPConfig(config); err != nil {
				return err
			}

			// Create and run HTTP tester
			tester := NewHTTPTester(config)
			return tester.Run(cmd.Context())
		},
	}

	// Add HTTP-specific flags
	cmd.Flags().StringVarP(&config.Method, "method", "X", "GET", "HTTP method")
	cmd.Flags().StringArrayVarP(&config.Headers, "header", "H", []string{}, "HTTP headers (format: 'Key: Value')")
	cmd.Flags().StringVarP(&config.Body, "body", "d", "", "Request body")
	cmd.Flags().StringVar(&config.ContentType, "content-type", "application/json", "Content-Type header")

	// Load parameters
	cmd.Flags().IntVarP(&config.Concurrency, "concurrency", "c", 1, "Number of concurrent workers")
	cmd.Flags().IntVarP(&config.TotalRequests, "requests", "n", 100, "Total number of requests (0 for duration-based)")
	cmd.Flags().DurationVarP(&config.Duration, "duration", "t", 30*time.Second, "Test duration")
	cmd.Flags().IntVar(&config.RateLimit, "rate-limit", 0, "Rate limit (requests per second, 0 for unlimited)")

	// Connection settings
	cmd.Flags().DurationVar(&config.Timeout, "timeout", 30*time.Second, "Request timeout")
	cmd.Flags().BoolVar(&config.KeepAlive, "keep-alive", true, "Use HTTP keep-alive")
	cmd.Flags().BoolVar(&config.HTTP2, "http2", true, "Use HTTP/2")
	cmd.Flags().BoolVar(&config.InsecureTLS, "insecure", false, "Skip TLS certificate verification")

	// Advanced patterns
	cmd.Flags().DurationVar(&config.RampUp, "ramp-up", 5*time.Second, "Ramp up duration")
	cmd.Flags().DurationVar(&config.RampDown, "ramp-down", 5*time.Second, "Ramp down duration")
	cmd.Flags().DurationVar(&config.ThinkTime, "think-time", 0, "Think time between requests")

	return cmd
}

// createGRPCCommand creates the gRPC load testing command
func createGRPCCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "grpc [TARGET]",
		Short: "Run gRPC load test against a target service",
		Long: `Run gRPC load test against a target gRPC service.

Examples:
  # Test GraphOps using reflection
  load-tester grpc localhost:13398 \
    --service ninaivalaigal.graphops.v1.GraphOpsService \
    --method ExecuteQuery \
    --data '{"query":"MATCH (n) RETURN n LIMIT 1"}' \
    --concurrency 50 --requests 5000

  # Supply proto file instead of reflection
  load-tester grpc localhost:13398 \
    --method ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery \
    --proto ../../shared/contracts/graphops/v1/graphops.proto \
    --data-file payload.json --duration 60s`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			config.URL = args[0]

			if err := validateGRPCConfig(config); err != nil {
				return err
			}

			tester := NewGRPCTester(config)
			return tester.Run(cmd.Context())
		},
	}

	cmd.Flags().StringVar(&config.GRPCService, "service", "", "Fully qualified gRPC service name (optional if --method contains service)")
	cmd.Flags().StringVar(&config.GRPCMethod, "method", "", "gRPC method (e.g. ExecuteQuery or Service/Method)")
	cmd.Flags().StringVar(&config.ProtoFile, "proto", "", "Path to proto file (optional when using reflection)")
	cmd.Flags().StringArrayVarP(&config.Headers, "header", "H", []string{}, "gRPC metadata header (Key: Value)")
	cmd.Flags().StringVar(&config.Body, "data", "", "Inline JSON request payload for unary calls")
	cmd.Flags().StringVar(&config.BodyFile, "data-file", "", "Path to JSON payload file")
	cmd.Flags().IntVarP(&config.Concurrency, "concurrency", "c", 1, "Number of concurrent workers")
	cmd.Flags().IntVarP(&config.TotalRequests, "requests", "n", 0, "Total number of requests (0 to use duration)")
	cmd.Flags().DurationVarP(&config.Duration, "duration", "t", 30*time.Second, "Test duration when --requests is 0")
	cmd.Flags().IntVar(&config.RateLimit, "rps", 0, "Requests per second limit (0 for unlimited)")
	cmd.Flags().DurationVar(&config.Timeout, "timeout", 30*time.Second, "Per-request timeout")
	cmd.Flags().BoolVar(&config.GRPCPlaintext, "plaintext", true, "Use plaintext (disable TLS)")

	return cmd
}

// createWebSocketCommand creates the WebSocket load testing command
func createWebSocketCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "ws [URL]",
		Short: "Run WebSocket load test against a target URL",
		Long: `Run WebSocket load test against a target WebSocket endpoint.

Examples:
  # Basic WebSocket test
  load-tester ws ws://localhost:8080/ws --concurrency 10 --duration 60s

  # WebSocket with custom protocol
  load-tester ws ws://localhost:8080/chat \
    --protocol "chat-v1" \
    --message-interval 1s \
    --concurrency 100`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			config.URL = args[0]
			color.Yellow("🚧 WebSocket load testing coming soon!")
			return nil
		},
	}

	cmd.Flags().StringVar(&config.WSProtocol, "protocol", "", "WebSocket protocol")
	cmd.Flags().StringVar(&config.WSOrigin, "origin", "", "WebSocket origin")
	cmd.Flags().DurationVar(&config.MessageInterval, "message-interval", 1*time.Second, "Interval between messages")

	return cmd
}

// createScenarioCommand creates the scenario-based testing command
func createScenarioCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "scenario [FILE]",
		Short: "Run load test based on a scenario file",
		Long: `Run load test based on a JSON scenario configuration file.

The scenario file should contain test targets, endpoints, and parameters.

Examples:
  # Run predefined scenario
  load-tester scenario grpc-gateway.json

  # Run with custom variables
  load-tester scenario test.json --var "HOST=localhost" --var "TOKEN=abc123"`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			config.ScenarioFile = args[0]

			// Load and execute scenario
			return runScenario(cmd.Context(), config.ScenarioFile)
		},
	}

	cmd.Flags().StringToStringVar(&config.Variables, "var", make(map[string]string), "Scenario variables (key=value)")
	cmd.Flags().IntVarP(&config.Concurrency, "concurrency", "c", config.Concurrency, "Base concurrency per endpoint (weight adjusted)")
	cmd.Flags().IntVar(&config.TotalRequests, "requests", 0, "Total requests per endpoint (0 for duration-based)")
	cmd.Flags().DurationVarP(&config.Duration, "duration", "t", config.Duration, "Per-endpoint test duration (ignored if --requests > 0)")
	cmd.Flags().IntVar(&config.RateLimit, "rate-limit", config.RateLimit, "Base rate limit (requests/sec) per endpoint (weight adjusted)")
	cmd.Flags().DurationVar(&config.ThinkTime, "think-time", config.ThinkTime, "Think time between requests")

	return cmd
}

// createMetricsCommand creates the metrics server command
func createMetricsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "metrics",
		Short: "Start Prometheus metrics server",
		Long: `Start a Prometheus metrics server to expose load testing metrics.

The metrics server exposes various metrics that can be scraped by Prometheus
and visualized in Grafana dashboards.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			color.Cyan("🚀 Starting Prometheus metrics server on %s", config.MetricsAddr)
			color.Yellow("🚧 Metrics server coming soon!")
			return nil
		},
	}

	return cmd
}

// createServerCommand creates the load testing server command
func createServerCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "server",
		Short: "Start load testing server for distributed testing",
		Long: `Start a load testing server that can coordinate distributed load tests
across multiple nodes.

This enables running large-scale load tests that exceed the capacity
of a single machine.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			color.Cyan("🚀 Starting load testing server")
			color.Yellow("🚧 Distributed server coming soon!")
			return nil
		},
	}

	return cmd
}

// validateHTTPConfig validates the HTTP configuration
func validateHTTPConfig(config *LoadTestConfig) error {
	if config.URL == "" {
		return fmt.Errorf("URL is required")
	}

	if config.Concurrency <= 0 {
		return fmt.Errorf("concurrency must be greater than 0")
	}

	if config.TotalRequests < 0 {
		return fmt.Errorf("total requests cannot be negative")
	}

	if config.TotalRequests == 0 && config.Duration <= 0 {
		return fmt.Errorf("either total requests or duration must be specified")
	}

	// Validate HTTP method
	validMethods := []string{"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
	methodValid := false
	for _, method := range validMethods {
		if strings.ToUpper(config.Method) == method {
			config.Method = method
			methodValid = true
			break
		}
	}
	if !methodValid {
		return fmt.Errorf("invalid HTTP method: %s", config.Method)
	}

	return nil
}

func validateGRPCConfig(config *LoadTestConfig) error {
	if config.URL == "" {
		return fmt.Errorf("target address is required")
	}

	if config.Concurrency <= 0 {
		return fmt.Errorf("concurrency must be greater than 0")
	}

	if config.TotalRequests <= 0 && config.Duration <= 0 {
		return fmt.Errorf("either total requests (--requests) or duration (--duration) must be specified")
	}

	if config.Timeout <= 0 {
		config.Timeout = 30 * time.Second
	}

	return nil
}

// runScenario executes a scenario-based load test
func runScenario(ctx context.Context, scenarioFile string) error {
	color.Cyan("📋 Loading scenario from: %s", scenarioFile)

	// Check if it's a predefined scenario
	targets := GetNinaivalaigalTargets()
	profiles := GetDefaultProfiles()

	// Check for predefined scenarios
	switch scenarioFile {
	case "grpc-gateway", "gateway":
		return runPredefinedScenario(ctx, "grpc-gateway", targets[0], profiles[5])
	case "smoke":
		return runPredefinedScenario(ctx, "smoke", targets[0], profiles[0])
	case "load":
		return runPredefinedScenario(ctx, "load", targets[0], profiles[1])
	case "stress":
		return runPredefinedScenario(ctx, "stress", targets[0], profiles[2])
	case "spike":
		return runPredefinedScenario(ctx, "spike", targets[0], profiles[3])
	case "endurance":
		return runPredefinedScenario(ctx, "endurance", targets[0], profiles[4])
	}

	// Try to load from file
	if _, err := os.Stat(scenarioFile); os.IsNotExist(err) {
		color.Red("❌ Scenario file not found: %s", scenarioFile)
		color.White("\nAvailable predefined scenarios:")
		for _, profile := range profiles {
			color.White("  • %s - %s", profile.Name, profile.Description)
		}
		return err
	}

	// Load custom scenario file
	data, err := os.ReadFile(scenarioFile)
	if err != nil {
		return fmt.Errorf("failed to read scenario file: %w", err)
	}

	var target TestTarget
	if err := json.Unmarshal(data, &target); err != nil {
		return fmt.Errorf("failed to parse scenario file: %w", err)
	}

	color.Green("✅ Loaded scenario: %s", target.Name)
	return runTargetScenario(ctx, target)
}

// runPredefinedScenario runs a predefined scenario
func runPredefinedScenario(ctx context.Context, name string, target TestTarget, profile TestProfile) error {
	color.Cyan("🎯 Running predefined scenario: %s", name)
	color.White("Description: %s", profile.Description)
	color.White("Target: %s", target.BaseURL)

	// Create config from profile
	testConfig := profile.Config
	testConfig.URL = target.BaseURL

	return runTargetScenarioWithConfig(ctx, target, testConfig)
}

// runTargetScenarioWithConfig executes a test scenario with given config
func runTargetScenarioWithConfig(ctx context.Context, target TestTarget, testConfig LoadTestConfig) error {
	color.Cyan("🚀 Starting scenario test against %s", target.Name)

	// Test each endpoint
	for i, endpoint := range target.Endpoints {
		color.White("\n📍 Testing endpoint %d/%d: %s %s",
			i+1, len(target.Endpoints), endpoint.Method, endpoint.Path)

		// Configure for this endpoint
		endpointConfig := testConfig
		endpointConfig.URL = target.BaseURL + endpoint.Path
		endpointConfig.Method = endpoint.Method
		endpointConfig.Body = endpoint.Body

		// Set headers
		headers := make([]string, 0, len(target.Headers)+len(endpoint.Headers))
		for key, value := range target.Headers {
			headers = append(headers, fmt.Sprintf("%s: %s", key, value))
		}
		for key, value := range endpoint.Headers {
			headers = append(headers, fmt.Sprintf("%s: %s", key, value))
		}
		endpointConfig.Headers = headers

		// Use weight for total requests if specified, otherwise default
		if endpoint.Weight > 0 {
			endpointConfig.TotalRequests = endpoint.Weight
		} else if endpointConfig.TotalRequests == 0 {
			endpointConfig.TotalRequests = 10 // Default
		}

		tester := NewHTTPTester(&endpointConfig)
		if err := tester.Run(ctx); err != nil {
			color.Red("❌ Endpoint failed: %v", err)
			// Continue with other endpoints
		}
	}

	color.Green("\n✅ Scenario test completed!")
	return nil
}

// runTargetScenario executes a test scenario against a target
func runTargetScenario(ctx context.Context, target TestTarget) error {
	// Use default config (original logic preserved)
	defaultConfig := NewLoadTestConfig()
	return runTargetScenarioWithConfig(ctx, target, *defaultConfig)
}

// Add helper commands for quick testing
func init() {
	// Add a quick test command
	quickCmd := &cobra.Command{
		Use:   "quick [TARGET]",
		Short: "Quick smoke test with minimal load",
		Long:  "Run a quick smoke test to verify service availability",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			url := "http://localhost:8080/health"
			if len(args) > 0 {
				url = args[0]
			}

			color.Cyan("🔍 Running quick smoke test on: %s", url)

			quickConfig := NewLoadTestConfig()
			quickConfig.URL = url
			quickConfig.Concurrency = 1
			quickConfig.TotalRequests = 5
			quickConfig.Duration = 10 * time.Second
			quickConfig.Timeout = 5 * time.Second

			tester := NewHTTPTester(quickConfig)
			return tester.Run(cmd.Context())
		},
	}

	// This will be added to rootCmd in main()
	_ = quickCmd
}

// createValidateCommand creates a command to validate load tester functionality
func createValidateCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "validate [BASE_URL]",
		Short: "Validate load tester functionality",
		Long:  "Run comprehensive validation tests to ensure load tester is working correctly",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			baseURL := "http://localhost:8080"
			if len(args) > 0 {
				baseURL = args[0]
			}

			validator := NewValidateTester(baseURL)
			return validator.RunValidation(cmd.Context())
		},
	}
}
