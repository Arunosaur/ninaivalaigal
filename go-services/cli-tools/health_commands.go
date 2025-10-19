package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/briandowns/spinner"
	"github.com/fatih/color"
	"github.com/go-resty/resty/v2"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// HealthStatus represents the health status of a service
type HealthStatus struct {
	Service      string                 `json:"service"`
	Status       string                 `json:"status"`
	URL          string                 `json:"url"`
	ResponseTime time.Duration          `json:"response_time"`
	StatusCode   int                    `json:"status_code"`
	Error        string                 `json:"error,omitempty"`
	Details      map[string]interface{} `json:"details,omitempty"`
	Timestamp    time.Time              `json:"timestamp"`
}

// ServiceDefinition defines a service to check
type ServiceDefinition struct {
	Name         string
	URL          string
	HealthPath   string
	Timeout      time.Duration
	ExpectedCode int
}

// createHealthCommand creates the health monitoring command
func createHealthCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "health",
		Short:   "Service health monitoring",
		Long:    "Monitor health and availability of Ninaivalaigal services",
		Aliases: []string{"status", "ping"},
	}

	cmd.AddCommand(
		createHealthCheckCommand(),
		createHealthWatchCommand(),
		createHealthDetailCommand(),
		createHealthSummaryCommand(),
	)

	return cmd
}

// createHealthCheckCommand checks health of all services
func createHealthCheckCommand() *cobra.Command {
	var (
		services   []string
		timeout    int
		parallel   bool
		jsonOutput bool
	)

	cmd := &cobra.Command{
		Use:   "check [SERVICES...]",
		Short: "Check service health",
		Long:  "Check health status of specified services or all services",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// Get service definitions
			serviceDefs := getServiceDefinitions()

			// Filter services if specified
			if len(services) > 0 {
				filtered := make([]ServiceDefinition, 0)
				for _, name := range services {
					for _, def := range serviceDefs {
						if def.Name == name {
							filtered = append(filtered, def)
							break
						}
					}
				}
				serviceDefs = filtered
			}

			if len(serviceDefs) == 0 {
				return fmt.Errorf("no services to check")
			}

			// Show spinner
			s := spinner.New(spinner.CharSets[14], 100*time.Millisecond)
			s.Suffix = " Checking service health..."
			s.Start()

			// Check health
			var results []HealthStatus
			if parallel {
				results = checkHealthParallel(serviceDefs, time.Duration(timeout)*time.Second)
			} else {
				results = checkHealthSequential(serviceDefs, time.Duration(timeout)*time.Second)
			}

			s.Stop()

			// Display results
			if jsonOutput {
				data, _ := json.MarshalIndent(results, "", "  ")
				fmt.Println(string(data))
			} else {
				displayHealthResults(results)
			}

			// Return error if any service is unhealthy
			for _, result := range results {
				if result.Status != "healthy" {
					return fmt.Errorf("one or more services are unhealthy")
				}
			}

			return nil
		},
	}

	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to check (memory, graphops, gateway)")
	cmd.Flags().IntVarP(&timeout, "timeout", "t", 10, "Timeout in seconds")
	cmd.Flags().BoolVarP(&parallel, "parallel", "p", true, "Check services in parallel")
	cmd.Flags().BoolVar(&jsonOutput, "json", false, "Output in JSON format")

	return cmd
}

// createHealthWatchCommand continuously monitors health
func createHealthWatchCommand() *cobra.Command {
	var (
		interval int
		services []string
		count    int
	)

	cmd := &cobra.Command{
		Use:   "watch [SERVICES...]",
		Short: "Watch service health",
		Long:  "Continuously monitor service health with specified interval",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// Get service definitions
			serviceDefs := getServiceDefinitions()

			// Filter services if specified
			if len(services) > 0 {
				filtered := make([]ServiceDefinition, 0)
				for _, name := range services {
					for _, def := range serviceDefs {
						if def.Name == name {
							filtered = append(filtered, def)
							break
						}
					}
				}
				serviceDefs = filtered
			}

			color.Cyan("👁️  Watching service health (interval: %ds, count: %d)", interval, count)
			color.Yellow("Press Ctrl+C to stop\n")

			// Watch loop
			for i := 0; count == 0 || i < count; i++ {
				if i > 0 {
					time.Sleep(time.Duration(interval) * time.Second)
				}

				// Check health
				results := checkHealthParallel(serviceDefs, 10*time.Second)

				// Clear screen and show results
				fmt.Printf("\n%s Health Check #%d\n",
					color.CyanString("🔍"), i+1)
				displayHealthResults(results)

				// Show timestamp
				color.Magenta("Last updated: %s\n", time.Now().Format("15:04:05"))
			}

			return nil
		},
	}

	cmd.Flags().IntVarP(&interval, "interval", "i", 30, "Check interval in seconds")
	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to watch")
	cmd.Flags().IntVarP(&count, "count", "c", 0, "Number of checks (0 for infinite)")

	return cmd
}

// createHealthDetailCommand shows detailed health information
func createHealthDetailCommand() *cobra.Command {
	var service string

	cmd := &cobra.Command{
		Use:   "detail [SERVICE]",
		Short: "Show detailed health information",
		Long:  "Show comprehensive health information for a specific service",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				service = args[0]
			}

			if service == "" {
				return fmt.Errorf("service name is required")
			}

			// Get service definition
			serviceDefs := getServiceDefinitions()
			var serviceDef *ServiceDefinition
			for _, def := range serviceDefs {
				if def.Name == service {
					serviceDef = &def
					break
				}
			}

			if serviceDef == nil {
				return fmt.Errorf("unknown service: %s", service)
			}

			// Show spinner
			s := spinner.New(spinner.CharSets[14], 100*time.Millisecond)
			s.Suffix = fmt.Sprintf(" Checking %s health...", service)
			s.Start()

			// Check detailed health
			result := checkDetailedHealth(*serviceDef)
			s.Stop()

			// Display detailed results
			displayDetailedHealth(result)

			return nil
		},
	}

	cmd.Flags().StringVarP(&service, "service", "s", "", "Service to check")

	return cmd
}

// createHealthSummaryCommand shows health summary
func createHealthSummaryCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "summary",
		Short: "Show health summary",
		Long:  "Show a summary of all service health statuses",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Get all services
			serviceDefs := getServiceDefinitions()

			// Show spinner
			s := spinner.New(spinner.CharSets[14], 100*time.Millisecond)
			s.Suffix = " Checking all services..."
			s.Start()

			// Check health
			results := checkHealthParallel(serviceDefs, 10*time.Second)
			s.Stop()

			// Calculate summary
			healthy := 0
			unhealthy := 0
			unknown := 0

			for _, result := range results {
				switch result.Status {
				case "healthy":
					healthy++
				case "unhealthy":
					unhealthy++
				default:
					unknown++
				}
			}

			// Display summary
			color.Cyan("📊 Health Summary")
			fmt.Printf("\n")

			color.Green("✅ Healthy: %d", healthy)
			color.Red("❌ Unhealthy: %d", unhealthy)
			if unknown > 0 {
				color.Yellow("❓ Unknown: %d", unknown)
			}

			total := len(results)
			if total > 0 {
				healthPercentage := float64(healthy) / float64(total) * 100
				fmt.Printf("\n")
				if healthPercentage == 100 {
					color.Green("🎉 All services are healthy (%.1f%%)", healthPercentage)
				} else if healthPercentage >= 80 {
					color.Yellow("⚠️  Most services are healthy (%.1f%%)", healthPercentage)
				} else {
					color.Red("🚨 Many services are unhealthy (%.1f%%)", healthPercentage)
				}
			}

			// Show problematic services
			if unhealthy > 0 || unknown > 0 {
				fmt.Printf("\n\n%s Problematic Services:\n", color.RedString("🚨"))
				for _, result := range results {
					if result.Status != "healthy" {
						color.Red("  • %s: %s", result.Service, result.Status)
						if result.Error != "" {
							color.Red("    Error: %s", result.Error)
						}
					}
				}
			}

			return nil
		},
	}

	return cmd
}

// Helper functions

// getServiceDefinitions returns all service definitions
func getServiceDefinitions() []ServiceDefinition {
	return []ServiceDefinition{
		{
			Name:         "gateway",
			URL:          viper.GetString("services.gateway.url"),
			HealthPath:   "/health",
			Timeout:      10 * time.Second,
			ExpectedCode: http.StatusOK,
		},
		{
			Name:         "memory",
			URL:          viper.GetString("services.memory.url"),
			HealthPath:   "/api/v1/memory/health",
			Timeout:      10 * time.Second,
			ExpectedCode: http.StatusOK,
		},
		{
			Name:         "graphops",
			URL:          viper.GetString("services.graphops.url"),
			HealthPath:   "/api/v1/graph/health",
			Timeout:      10 * time.Second,
			ExpectedCode: http.StatusOK,
		},
	}
}

// checkHealthSequential checks services sequentially
func checkHealthSequential(services []ServiceDefinition, timeout time.Duration) []HealthStatus {
	var results []HealthStatus

	for _, service := range services {
		result := checkServiceHealth(service, timeout)
		results = append(results, result)
	}

	return results
}

// checkHealthParallel checks services in parallel
func checkHealthParallel(services []ServiceDefinition, timeout time.Duration) []HealthStatus {
	var wg sync.WaitGroup
	results := make([]HealthStatus, len(services))

	for i, service := range services {
		wg.Add(1)
		go func(index int, svc ServiceDefinition) {
			defer wg.Done()
			results[index] = checkServiceHealth(svc, timeout)
		}(i, service)
	}

	wg.Wait()
	return results
}

// checkServiceHealth checks a single service health
func checkServiceHealth(service ServiceDefinition, timeout time.Duration) HealthStatus {
	start := time.Now()
	result := HealthStatus{
		Service:   service.Name,
		URL:       service.URL + service.HealthPath,
		Timestamp: start,
	}

	// Create HTTP client
	client := resty.New().SetTimeout(timeout)

	// Make request
	resp, err := client.R().Get(service.URL + service.HealthPath)
	result.ResponseTime = time.Since(start)

	if err != nil {
		result.Status = "unhealthy"
		result.Error = err.Error()
		result.StatusCode = 0
		return result
	}

	result.StatusCode = resp.StatusCode()

	// Check status code
	if resp.StatusCode() == service.ExpectedCode {
		result.Status = "healthy"
	} else {
		result.Status = "unhealthy"
		result.Error = fmt.Sprintf("unexpected status code: %d", resp.StatusCode())
	}

	// Try to parse response for details
	var details map[string]interface{}
	if err := json.Unmarshal(resp.Body(), &details); err == nil {
		result.Details = details
	}

	return result
}

// checkDetailedHealth performs detailed health check
func checkDetailedHealth(service ServiceDefinition) HealthStatus {
	result := checkServiceHealth(service, service.Timeout)

	// Add more detailed checks here if needed
	// For example, check specific endpoints, database connectivity, etc.

	return result
}

// displayHealthResults displays health check results
func displayHealthResults(results []HealthStatus) {
	if len(results) == 0 {
		color.Yellow("No services checked")
		return
	}

	// Create table
	table := tablewriter.NewWriter(color.Output)
	table.SetHeader([]string{"Service", "Status", "Response Time", "Status Code", "URL"})
	table.SetAutoFormatHeaders(true)
	table.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
	table.SetAlignment(tablewriter.ALIGN_LEFT)
	table.SetCenterSeparator("")
	table.SetColumnSeparator("")
	table.SetRowSeparator("")
	table.SetHeaderLine(false)
	table.SetBorder(false)
	table.SetTablePadding("\t")
	table.SetNoWhiteSpace(true)

	for _, result := range results {
		// Format status with color
		var statusStr string
		switch result.Status {
		case "healthy":
			statusStr = color.GreenString("✅ %s", result.Status)
		case "unhealthy":
			statusStr = color.RedString("❌ %s", result.Status)
		default:
			statusStr = color.YellowString("❓ %s", result.Status)
		}

		// Format response time
		responseTime := fmt.Sprintf("%.0fms", float64(result.ResponseTime.Nanoseconds())/1e6)
		if result.ResponseTime > time.Second {
			responseTime = color.RedString(responseTime)
		} else if result.ResponseTime > 500*time.Millisecond {
			responseTime = color.YellowString(responseTime)
		} else {
			responseTime = color.GreenString(responseTime)
		}

		// Format status code
		statusCode := fmt.Sprintf("%d", result.StatusCode)
		if result.StatusCode == 0 {
			statusCode = color.RedString("N/A")
		} else if result.StatusCode >= 200 && result.StatusCode < 300 {
			statusCode = color.GreenString(statusCode)
		} else {
			statusCode = color.RedString(statusCode)
		}

		table.Append([]string{
			result.Service,
			statusStr,
			responseTime,
			statusCode,
			result.URL,
		})
	}

	table.Render()

	// Show errors if any
	for _, result := range results {
		if result.Error != "" {
			color.Red("❌ %s: %s", result.Service, result.Error)
		}
	}
}

// displayDetailedHealth displays detailed health information
func displayDetailedHealth(result HealthStatus) {
	color.Cyan("🔍 Detailed Health Check: %s", result.Service)
	fmt.Printf("\n")

	// Basic info
	color.White("URL: %s", result.URL)
	color.White("Timestamp: %s", result.Timestamp.Format("2006-01-02 15:04:05"))

	// Status
	switch result.Status {
	case "healthy":
		color.Green("Status: ✅ %s", result.Status)
	case "unhealthy":
		color.Red("Status: ❌ %s", result.Status)
	default:
		color.Yellow("Status: ❓ %s", result.Status)
	}

	// Performance
	responseTime := float64(result.ResponseTime.Nanoseconds()) / 1e6
	if result.ResponseTime > time.Second {
		color.Red("Response Time: %.0fms (slow)", responseTime)
	} else if result.ResponseTime > 500*time.Millisecond {
		color.Yellow("Response Time: %.0fms (moderate)", responseTime)
	} else {
		color.Green("Response Time: %.0fms (fast)", responseTime)
	}

	// Status code
	if result.StatusCode == 0 {
		color.Red("Status Code: N/A (connection failed)")
	} else if result.StatusCode >= 200 && result.StatusCode < 300 {
		color.Green("Status Code: %d (success)", result.StatusCode)
	} else {
		color.Red("Status Code: %d (error)", result.StatusCode)
	}

	// Error details
	if result.Error != "" {
		color.Red("Error: %s", result.Error)
	}

	// Additional details from response
	if len(result.Details) > 0 {
		fmt.Printf("\n%s Response Details:\n", color.BlueString("📋"))
		for key, value := range result.Details {
			fmt.Printf("  %s: %v\n", key, value)
		}
	}
}
