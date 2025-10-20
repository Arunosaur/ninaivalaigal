package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

// Version info
const (
	Version = "1.0.0"
	AppName = "Ninaivalaigal Load Tester"
)

// Global configuration
var config *LoadTestConfig

func main() {
	// Setup colored output
	color.NoColor = false

	// Initialize global configuration before creating commands so flag bindings are safe
	config = NewLoadTestConfig()

	// Create root command
	rootCmd := &cobra.Command{
		Use:   "load-tester",
		Short: "High-performance load testing tool for Ninaivalaigal services",
		Long: fmt.Sprintf(`%s v%s

A comprehensive load testing tool designed specifically for the Ninaivalaigal
microservice architecture. Supports HTTP, gRPC, WebSocket, and custom protocols
with advanced metrics collection and real-time reporting.

Features:
  • High-concurrency testing (10,000+ concurrent connections)
  • Multiple protocol support (HTTP/REST, gRPC, WebSocket)
  • Real-time metrics and visualization
  • Distributed load testing capabilities
  • Custom scenario scripting
  • Prometheus metrics export
  • Advanced request patterns and rate limiting`, AppName, Version),
		Version: Version,
	}

	// Global flags
	rootCmd.PersistentFlags().BoolVar(&config.Verbose, "verbose", false, "Enable verbose logging")
	rootCmd.PersistentFlags().StringVar(&config.OutputFormat, "output", "console", "Output format (console, json, prometheus)")
	rootCmd.PersistentFlags().StringVar(&config.MetricsAddr, "metrics-addr", ":9090", "Prometheus metrics server address")

	// Add subcommands after config initialization so nested commands can safely access it
	rootCmd.AddCommand(
		createHTTPCommand(),
		createGRPCCommand(),
		createWebSocketCommand(),
		createScenarioCommand(),
		createMetricsCommand(),
		createServerCommand(),
		createValidateCommand(),
	)

	// Setup graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle signals
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-signalChan
		color.Yellow("\n🛑 Received shutdown signal, stopping load tests...")
		cancel()
		time.Sleep(2 * time.Second)
		os.Exit(0)
	}()

	// Execute command
	if err := rootCmd.ExecuteContext(ctx); err != nil {
		color.Red("❌ Error: %v", err)
		os.Exit(1)
	}
}

// Print banner
func init() {
	banner := color.New(color.FgCyan, color.Bold)
	if _, err := banner.Printf(`
╔══════════════════════════════════════════════╗
║          NINAIVALAIGAL LOAD TESTER           ║
║              Developer A Task #37            ║
║         High-Performance Testing Tool        ║
╚══════════════════════════════════════════════╝

`); err != nil {
		log.Printf("⚠️ Failed to print banner: %v\n", err)
	}

	// Initialize logger
	log.SetFlags(log.LstdFlags | log.Lshortfile)
}
