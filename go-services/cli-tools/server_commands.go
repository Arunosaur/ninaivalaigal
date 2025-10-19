package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

// createServerCommand creates the server management command
func createServerCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "server",
		Short:   "Server management",
		Long:    "Start, stop, and manage Ninaivalaigal services",
		Aliases: []string{"srv", "service"},
	}

	cmd.AddCommand(
		createServerStartCommand(),
		createServerStopCommand(),
		createServerRestartCommand(),
		createServerStatusCommand(),
		createServerLogsCommand(),
		createServerBuildCommand(),
	)

	return cmd
}

// createServerStartCommand starts services
func createServerStartCommand() *cobra.Command {
	var (
		services []string
		detach   bool
		rebuild  bool
		env      string
	)

	cmd := &cobra.Command{
		Use:   "start [SERVICES...]",
		Short: "Start services",
		Long:  "Start one or more Ninaivalaigal services",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// If no services specified, start all
			if len(services) == 0 {
				services = []string{"gateway", "load-tester"}
			}

			color.Cyan("🚀 Starting services: %s", strings.Join(services, ", "))

			// Build services if requested
			if rebuild {
				color.Yellow("🔨 Building services first...")
				if err := buildServices(services); err != nil {
					return fmt.Errorf("failed to build services: %w", err)
				}
			}

			// Start each service
			for _, service := range services {
				if err := startService(service, detach, env); err != nil {
					color.Red("❌ Failed to start %s: %v", service, err)
					return err
				}
				color.Green("✅ Started %s", service)
			}

			if detach {
				color.Blue("📋 Services started in background")
				color.Yellow("💡 Use 'nina server logs' to view logs")
				color.Yellow("💡 Use 'nina server status' to check status")
			} else {
				color.Blue("📋 Services running in foreground")
				color.Yellow("💡 Press Ctrl+C to stop services")
			}

			return nil
		},
	}

	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to start")
	cmd.Flags().BoolVarP(&detach, "detach", "d", false, "Run in background")
	cmd.Flags().BoolVarP(&rebuild, "rebuild", "r", false, "Rebuild services before starting")
	cmd.Flags().StringVarP(&env, "env", "e", "local", "Environment profile")

	return cmd
}

// createServerStopCommand stops services
func createServerStopCommand() *cobra.Command {
	var (
		services []string
		force    bool
	)

	cmd := &cobra.Command{
		Use:   "stop [SERVICES...]",
		Short: "Stop services",
		Long:  "Stop one or more running services",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// If no services specified, stop all
			if len(services) == 0 {
				services = []string{"gateway", "load-tester"}
			}

			color.Cyan("🛑 Stopping services: %s", strings.Join(services, ", "))

			// Stop each service
			for _, service := range services {
				if err := stopService(service, force); err != nil {
					color.Red("❌ Failed to stop %s: %v", service, err)
					// Continue with other services
				} else {
					color.Green("✅ Stopped %s", service)
				}
			}

			return nil
		},
	}

	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to stop")
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Force stop services")

	return cmd
}

// createServerRestartCommand restarts services
func createServerRestartCommand() *cobra.Command {
	var (
		services []string
		rebuild  bool
	)

	cmd := &cobra.Command{
		Use:   "restart [SERVICES...]",
		Short: "Restart services",
		Long:  "Restart one or more services",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// If no services specified, restart all
			if len(services) == 0 {
				services = []string{"gateway", "load-tester"}
			}

			color.Cyan("🔄 Restarting services: %s", strings.Join(services, ", "))

			// Stop services first
			for _, service := range services {
				if err := stopService(service, false); err != nil {
					color.Yellow("⚠️  Failed to stop %s (may not be running): %v", service, err)
				}
			}

			// Wait a moment
			time.Sleep(2 * time.Second)

			// Build if requested
			if rebuild {
				color.Yellow("🔨 Rebuilding services...")
				if err := buildServices(services); err != nil {
					return fmt.Errorf("failed to build services: %w", err)
				}
			}

			// Start services
			for _, service := range services {
				if err := startService(service, true, "local"); err != nil {
					color.Red("❌ Failed to start %s: %v", service, err)
					return err
				}
				color.Green("✅ Restarted %s", service)
			}

			color.Blue("📋 Services restarted successfully")
			return nil
		},
	}

	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to restart")
	cmd.Flags().BoolVarP(&rebuild, "rebuild", "r", false, "Rebuild services before restarting")

	return cmd
}

// createServerStatusCommand shows service status
func createServerStatusCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "status",
		Short: "Show service status",
		Long:  "Display status of all managed services",
		RunE: func(cmd *cobra.Command, args []string) error {
			color.Cyan("📊 Service Status")

			services := []string{"gateway", "load-tester"}

			for _, service := range services {
				status := getServiceStatus(service)
				displayServiceStatus(service, status)
			}

			return nil
		},
	}

	return cmd
}

// createServerLogsCommand shows service logs
func createServerLogsCommand() *cobra.Command {
	var (
		service string
		follow  bool
		tail    int
	)

	cmd := &cobra.Command{
		Use:   "logs [SERVICE]",
		Short: "Show service logs",
		Long:  "Display logs for a specific service",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				service = args[0]
			}

			if service == "" {
				service = "gateway"
			}

			color.Cyan("📋 Showing logs for: %s", service)

			return showServiceLogs(service, follow, tail)
		},
	}

	cmd.Flags().StringVarP(&service, "service", "s", "", "Service to show logs for")
	cmd.Flags().BoolVarP(&follow, "follow", "f", false, "Follow log output")
	cmd.Flags().IntVarP(&tail, "tail", "t", 100, "Number of lines to show")

	return cmd
}

// createServerBuildCommand builds services
func createServerBuildCommand() *cobra.Command {
	var (
		services []string
		clean    bool
		parallel bool
	)

	cmd := &cobra.Command{
		Use:   "build [SERVICES...]",
		Short: "Build services",
		Long:  "Build one or more services",
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				services = args
			}

			// If no services specified, build all
			if len(services) == 0 {
				services = []string{"gateway", "load-tester"}
			}

			color.Cyan("🔨 Building services: %s", strings.Join(services, ", "))

			if clean {
				color.Yellow("🧹 Cleaning before build...")
				if err := cleanServices(services); err != nil {
					return fmt.Errorf("failed to clean services: %w", err)
				}
			}

			if err := buildServices(services); err != nil {
				return fmt.Errorf("failed to build services: %w", err)
			}

			color.Green("✅ Build completed successfully")
			return nil
		},
	}

	cmd.Flags().StringSliceVarP(&services, "services", "s", []string{}, "Services to build")
	cmd.Flags().BoolVar(&clean, "clean", false, "Clean before building")
	cmd.Flags().BoolVar(&parallel, "parallel", false, "Build services in parallel")

	return cmd
}

// Helper functions

// ServiceStatus represents the status of a service
type ServiceStatus struct {
	Name    string
	Running bool
	PID     int
	Port    int
	URL     string
	Uptime  time.Duration
	Error   string
}

// startService starts a specific service
func startService(service string, detach bool, env string) error {
	var cmd *exec.Cmd
	var dir string

	switch service {
	case "gateway", "grpc-gateway":
		dir = "../grpc-gateway"
		if _, err := os.Stat(filepath.Join(dir, "grpc-gateway")); err == nil {
			cmd = exec.Command("./grpc-gateway")
		} else {
			// Try to build first
			buildCmd := exec.Command("make", "build")
			buildCmd.Dir = dir
			if err := buildCmd.Run(); err != nil {
				return fmt.Errorf("failed to build gateway: %w", err)
			}
			cmd = exec.Command("./grpc-gateway")
		}

	case "load-tester", "loadtester":
		dir = "../load-tester"
		if _, err := os.Stat(filepath.Join(dir, "load-tester")); err == nil {
			cmd = exec.Command("./load-tester", "server", "--port", "8083")
		} else {
			// Try to build first
			buildCmd := exec.Command("make", "build")
			buildCmd.Dir = dir
			if err := buildCmd.Run(); err != nil {
				return fmt.Errorf("failed to build load tester: %w", err)
			}
			cmd = exec.Command("./load-tester", "server", "--port", "8083")
		}

	default:
		return fmt.Errorf("unknown service: %s", service)
	}

	cmd.Dir = dir

	if detach {
		// Start in background
		if err := cmd.Start(); err != nil {
			return fmt.Errorf("failed to start service: %w", err)
		}

		// Write PID to file for later reference
		pidFile := filepath.Join(os.TempDir(), fmt.Sprintf("nina-%s.pid", service))
		pidContent := fmt.Sprintf("%d", cmd.Process.Pid)
		if err := os.WriteFile(pidFile, []byte(pidContent), 0644); err != nil {
			fmt.Printf("⚠️  Failed to write PID file: %v\n", err)
		}
	} else {
		// Run in foreground
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("service exited with error: %w", err)
		}
	}

	return nil
}

// stopService stops a specific service
func stopService(service string, force bool) error {
	pidFile := filepath.Join(os.TempDir(), fmt.Sprintf("nina-%s.pid", service))

	// Read PID file
	pidData, err := os.ReadFile(pidFile)
	if err != nil {
		return fmt.Errorf("service not running or PID file not found")
	}

	// Kill process
	killCmd := exec.Command("kill", string(pidData))
	if force {
		killCmd = exec.Command("kill", "-9", string(pidData))
	}

	if err := killCmd.Run(); err != nil {
		return fmt.Errorf("failed to stop service: %w", err)
	}

	// Remove PID file
	if err := os.Remove(pidFile); err != nil && !os.IsNotExist(err) {
		fmt.Printf("⚠️  Failed to remove PID file: %v\n", err)
	}

	return nil
}

// buildServices builds multiple services
func buildServices(services []string) error {
	for _, service := range services {
		color.Yellow("🔨 Building %s...", service)

		var dir string
		switch service {
		case "gateway", "grpc-gateway":
			dir = "../grpc-gateway"
		case "load-tester", "loadtester":
			dir = "../load-tester"
		default:
			color.Yellow("⚠️  Unknown service: %s, skipping", service)
			continue
		}

		buildCmd := exec.Command("make", "build")
		buildCmd.Dir = dir
		buildCmd.Stdout = os.Stdout
		buildCmd.Stderr = os.Stderr

		if err := buildCmd.Run(); err != nil {
			return fmt.Errorf("failed to build %s: %w", service, err)
		}

		color.Green("✅ Built %s", service)
	}

	return nil
}

// cleanServices cleans build artifacts
func cleanServices(services []string) error {
	for _, service := range services {
		var dir string
		switch service {
		case "gateway", "grpc-gateway":
			dir = "../grpc-gateway"
		case "load-tester", "loadtester":
			dir = "../load-tester"
		default:
			continue
		}

		cleanCmd := exec.Command("make", "clean")
		cleanCmd.Dir = dir
		if err := cleanCmd.Run(); err != nil {
			color.Yellow("⚠️  Failed to clean %s: %v", service, err)
		}
	}

	return nil
}

// getServiceStatus gets the status of a service
func getServiceStatus(service string) ServiceStatus {
	status := ServiceStatus{
		Name:    service,
		Running: false,
	}

	// Check if PID file exists
	pidFile := filepath.Join(os.TempDir(), fmt.Sprintf("nina-%s.pid", service))
	if pidData, err := os.ReadFile(pidFile); err == nil {
		// Check if process is actually running
		checkCmd := exec.Command("ps", "-p", string(pidData))
		if err := checkCmd.Run(); err == nil {
			status.Running = true

			// Try to determine port and URL
			switch service {
			case "gateway", "grpc-gateway":
				status.Port = 8080
				status.URL = "http://localhost:8080"
			case "load-tester":
				status.Port = 8083
				status.URL = "http://localhost:8083"
			}

			// Check if service is responding
			if status.URL != "" {
				client := &http.Client{Timeout: 2 * time.Second}
				if resp, err := client.Get(status.URL + "/health"); err == nil {
					if closeErr := resp.Body.Close(); closeErr != nil {
						fmt.Printf("⚠️  Failed to close response body: %v\n", closeErr)
					}
					if resp.StatusCode != 200 {
						status.Error = fmt.Sprintf("HTTP %d", resp.StatusCode)
					}
				} else {
					status.Error = "Not responding"
				}
			}
		}
	}

	return status
}

// displayServiceStatus displays the status of a service
func displayServiceStatus(service string, status ServiceStatus) {
	if status.Running {
		color.Green("✅ %s - Running", service)
		if status.URL != "" {
			color.Blue("   URL: %s", status.URL)
		}
		if status.Port > 0 {
			color.Blue("   Port: %d", status.Port)
		}
		if status.Error != "" {
			color.Yellow("   Warning: %s", status.Error)
		}
	} else {
		color.Red("❌ %s - Stopped", service)
	}
}

// showServiceLogs shows logs for a service
func showServiceLogs(service string, follow bool, tail int) error {
	logFile := filepath.Join(os.TempDir(), fmt.Sprintf("nina-%s.log", service))

	var cmd *exec.Cmd
	if follow {
		cmd = exec.Command("tail", "-f", fmt.Sprintf("-%d", tail), logFile)
	} else {
		cmd = exec.Command("tail", fmt.Sprintf("-%d", tail), logFile)
	}

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		// If tail fails, try to show what we can
		if data, err := os.ReadFile(logFile); err == nil {
			lines := strings.Split(string(data), "\n")
			start := len(lines) - tail
			if start < 0 {
				start = 0
			}

			for _, line := range lines[start:] {
				if line != "" {
					fmt.Println(line)
				}
			}
		} else {
			color.Yellow("⚠️  No logs found for %s", service)
		}
	}

	return nil
}
