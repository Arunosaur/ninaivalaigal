package main

import (
	"fmt"
	"os/exec"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// createLoadTestCommand creates the load testing command
func createLoadTestCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "loadtest",
		Short:   "Load testing operations",
		Long:    "Execute load tests against Ninaivalaigal services using the integrated load tester",
		Aliases: []string{"lt", "test"},
	}

	cmd.AddCommand(
		createLoadTestHTTPCommand(),
		createLoadTestScenarioCommand(),
		createLoadTestQuickCommand(),
		createLoadTestProfileCommand(),
		createLoadTestValidateCommand(),
	)

	return cmd
}

// createLoadTestHTTPCommand runs HTTP load tests
func createLoadTestHTTPCommand() *cobra.Command {
	var (
		url         string
		method      string
		concurrency int
		requests    int
		duration    string
		timeout     string
		headers     []string
		body        string
		profile     string
	)

	cmd := &cobra.Command{
		Use:   "http [URL]",
		Short: "Run HTTP load test",
		Long:  "Execute HTTP load test with configurable parameters",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				url = args[0]
			}

			if url == "" {
				// Use default gateway URL
				url = viper.GetString("services.gateway.url") + "/health"
			}

			// Build load tester command
			loadTesterCmd := []string{
				"../load-tester/load-tester",
				"http",
				"--url", url,
				"--method", method,
				"--concurrency", fmt.Sprintf("%d", concurrency),
				"--timeout", timeout,
			}

			if requests > 0 {
				loadTesterCmd = append(loadTesterCmd, "--requests", fmt.Sprintf("%d", requests))
			}
			if duration != "" {
				loadTesterCmd = append(loadTesterCmd, "--duration", duration)
			}
			if profile != "" {
				loadTesterCmd = append(loadTesterCmd, "--profile", profile)
			}

			// Add headers
			for _, header := range headers {
				loadTesterCmd = append(loadTesterCmd, "--header", header)
			}

			// Add body if provided
			if body != "" {
				loadTesterCmd = append(loadTesterCmd, "--body", body)
			}

			// Execute load test
			color.Cyan("🚀 Starting HTTP load test...")
			color.Yellow("Target: %s", url)
			color.Yellow("Concurrency: %d, Requests: %d, Duration: %s", concurrency, requests, duration)

			return executeLoadTester(loadTesterCmd)
		},
	}

	cmd.Flags().StringVarP(&url, "url", "u", "", "Target URL")
	cmd.Flags().StringVarP(&method, "method", "m", "GET", "HTTP method")
	cmd.Flags().IntVarP(&concurrency, "concurrency", "c", 10, "Concurrent connections")
	cmd.Flags().IntVarP(&requests, "requests", "r", 100, "Total requests (0 for duration-based)")
	cmd.Flags().StringVarP(&duration, "duration", "d", "", "Test duration (e.g., 30s, 5m)")
	cmd.Flags().StringVarP(&timeout, "timeout", "t", "30s", "Request timeout")
	cmd.Flags().StringArrayVarP(&headers, "header", "H", []string{}, "HTTP headers (key:value)")
	cmd.Flags().StringVarP(&body, "body", "b", "", "Request body")
	cmd.Flags().StringVarP(&profile, "profile", "p", "", "Load test profile (smoke, load, stress)")

	return cmd
}

// createLoadTestScenarioCommand runs scenario-based tests
func createLoadTestScenarioCommand() *cobra.Command {
	var (
		scenarioFile string
		concurrency  int
		duration     string
		baseURL      string
	)

	cmd := &cobra.Command{
		Use:   "scenario [FILE]",
		Short: "Run scenario-based load test",
		Long:  "Execute load test using a predefined scenario file",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				scenarioFile = args[0]
			}

			if scenarioFile == "" {
				scenarioFile = "../load-tester/scenarios/grpc-gateway.json"
			}

			// Build load tester command
			loadTesterCmd := []string{
				"../load-tester/load-tester",
				"scenario",
				"--file", scenarioFile,
				"--concurrency", fmt.Sprintf("%d", concurrency),
			}

			if duration != "" {
				loadTesterCmd = append(loadTesterCmd, "--duration", duration)
			}
			if baseURL != "" {
				loadTesterCmd = append(loadTesterCmd, "--base-url", baseURL)
			}

			// Execute load test
			color.Cyan("🎬 Starting scenario-based load test...")
			color.Yellow("Scenario: %s", scenarioFile)
			color.Yellow("Concurrency: %d, Duration: %s", concurrency, duration)

			return executeLoadTester(loadTesterCmd)
		},
	}

	cmd.Flags().StringVarP(&scenarioFile, "file", "f", "", "Scenario file")
	cmd.Flags().IntVarP(&concurrency, "concurrency", "c", 10, "Concurrent connections")
	cmd.Flags().StringVarP(&duration, "duration", "d", "60s", "Test duration")
	cmd.Flags().StringVarP(&baseURL, "base-url", "u", "", "Override base URL")

	return cmd
}

// createLoadTestQuickCommand runs quick smoke tests
func createLoadTestQuickCommand() *cobra.Command {
	var target string

	cmd := &cobra.Command{
		Use:   "quick [SERVICE]",
		Short: "Quick smoke test",
		Long:  "Run a quick smoke test against a service",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				target = args[0]
			}

			// Determine target URL
			var url string
			switch target {
			case "memory":
				url = viper.GetString("services.memory.url") + "/health"
			case "graph", "graphops":
				url = viper.GetString("services.graphops.url") + "/health"
			case "gateway":
				url = viper.GetString("services.gateway.url") + "/health"
			default:
				url = viper.GetString("services.gateway.url") + "/health"
			}

			// Build quick test command
			loadTesterCmd := []string{
				"../load-tester/load-tester",
				"quick",
				url,
			}

			// Execute quick test
			color.Cyan("⚡ Running quick smoke test...")
			color.Yellow("Target: %s", url)

			return executeLoadTester(loadTesterCmd)
		},
	}

	cmd.Flags().StringVarP(&target, "target", "t", "gateway", "Target service (memory, graph, gateway)")

	return cmd
}

// createLoadTestProfileCommand runs predefined test profiles
func createLoadTestProfileCommand() *cobra.Command {
	var (
		profile string
		target  string
		url     string
	)

	cmd := &cobra.Command{
		Use:   "profile [PROFILE]",
		Short: "Run predefined test profile",
		Long:  "Execute load test using a predefined profile (smoke, light, moderate, heavy, stress, endurance)",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				profile = args[0]
			}

			// Validate profile
			profiles := GetLoadTestProfiles()
			if _, exists := profiles[profile]; !exists {
				return fmt.Errorf("unknown profile: %s. Available: smoke, light, moderate, heavy, stress, endurance", profile)
			}

			// Determine target URL
			if url == "" {
				switch target {
				case "memory":
					url = viper.GetString("services.memory.url") + "/api/v1/memory/health"
				case "graph", "graphops":
					url = viper.GetString("services.graphops.url") + "/api/v1/graph/health"
				case "gateway":
					url = viper.GetString("services.gateway.url") + "/health"
				default:
					url = viper.GetString("services.gateway.url") + "/health"
				}
			}

			// Build profile test command
			loadTesterCmd := []string{
				"../load-tester/load-tester",
				"http",
				"--url", url,
				"--profile", profile,
			}

			// Execute profile test
			color.Cyan("📊 Running %s profile test...", profile)
			color.Yellow("Target: %s", url)

			// Show profile details
			profileConfig := profiles[profile].(map[string]interface{})
			if desc, ok := profileConfig["description"]; ok {
				color.Blue("Description: %s", desc)
			}

			return executeLoadTester(loadTesterCmd)
		},
	}

	cmd.Flags().StringVarP(&profile, "profile", "p", "smoke", "Test profile")
	cmd.Flags().StringVarP(&target, "target", "t", "gateway", "Target service")
	cmd.Flags().StringVarP(&url, "url", "u", "", "Override target URL")

	return cmd
}

// createLoadTestValidateCommand validates load tester
func createLoadTestValidateCommand() *cobra.Command {
	var baseURL string

	cmd := &cobra.Command{
		Use:   "validate [BASE_URL]",
		Short: "Validate load tester",
		Long:  "Validate load tester functionality and service connectivity",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				baseURL = args[0]
			}

			if baseURL == "" {
				baseURL = viper.GetString("services.gateway.url")
			}

			// Build validate command
			loadTesterCmd := []string{
				"../load-tester/load-tester",
				"validate",
				baseURL,
			}

			// Execute validation
			color.Cyan("🔍 Validating load tester functionality...")
			color.Yellow("Base URL: %s", baseURL)

			return executeLoadTester(loadTesterCmd)
		},
	}

	cmd.Flags().StringVarP(&baseURL, "base-url", "u", "", "Base URL for validation")

	return cmd
}

// executeLoadTester executes the load tester command
func executeLoadTester(cmdArgs []string) error {
	// Check if load tester exists
	loadTesterPath := cmdArgs[0]
	if _, err := exec.LookPath(loadTesterPath); err != nil {
		// Try relative path
		if cmdArgs[0] == "../load-tester/load-tester" {
			color.Yellow("⚠️  Load tester not found at %s", loadTesterPath)
			color.Yellow("💡 Building load tester...")

			// Build load tester
			buildCmd := exec.Command("make", "build")
			buildCmd.Dir = "../load-tester"
			if err := buildCmd.Run(); err != nil {
				return fmt.Errorf("failed to build load tester: %w", err)
			}

			color.Green("✅ Load tester built successfully")
		} else {
			return fmt.Errorf("load tester not found: %s", loadTesterPath)
		}
	}

	// Execute command
	color.Blue("🔧 Executing: %s", strings.Join(cmdArgs, " "))

	execCmd := exec.Command(cmdArgs[0], cmdArgs[1:]...)
	execCmd.Stdout = color.Output
	execCmd.Stderr = color.Error

	start := time.Now()
	err := execCmd.Run()
	duration := time.Since(start)

	if err != nil {
		color.Red("❌ Load test failed after %.2fs: %v", duration.Seconds(), err)
		return err
	}

	color.Green("✅ Load test completed successfully in %.2fs", duration.Seconds())
	return nil
}
