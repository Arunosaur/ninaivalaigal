package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// Version info
const (
	Version = "1.0.0"
	AppName = "Ninaivalaigal CLI Tools"
)

// Global configuration
var (
	cfgFile      string
	verbose      bool
	outputFormat string
	configDir    string
)

func main() {
	// Setup colored output
	color.NoColor = false

	// Create root command
	rootCmd := &cobra.Command{
		Use:   "nina",
		Short: "Comprehensive CLI tools for Ninaivalaigal services",
		Long: fmt.Sprintf(`%s v%s

A comprehensive command-line interface for managing and interacting with
Ninaivalaigal microservices. Provides unified access to Memory Service,
GraphOps Service, Load Testing, and system administration capabilities.

Features:
  • Memory management (store, search, analyze memories)
  • Graph operations (query, visualize, manage graph data)
  • Service monitoring and health checks
  • Load testing and performance validation
  • Configuration management and deployment tools
  • Interactive CLI with guided workflows`, AppName, Version),
		Version: Version,
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			return initConfig()
		},
	}

	// Add subcommands
	rootCmd.AddCommand(
		createMemoryCommand(),
		createGraphCommand(),
		createLoadTestCommand(),
		createHealthCommand(),
		createConfigCommand(),
		createServerCommand(),
		createInteractiveCommand(),
	)

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.nina.yaml)")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	rootCmd.PersistentFlags().StringVarP(&outputFormat, "output", "o", "table", "Output format (table, json, yaml)")
	rootCmd.PersistentFlags().StringVar(&configDir, "config-dir", "", "Configuration directory (default is $HOME/.nina)")

	// Initialize config
	cobra.OnInitialize(func() {
		if err := initConfig(); err != nil {
			color.Red("❌ Failed to initialize config: %v", err)
			os.Exit(1)
		}
	})

	// Setup graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle termination signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		color.Yellow("\n🛑 Received termination signal, shutting down gracefully...")
		cancel()
	}()

	// Execute root command
	if err := rootCmd.ExecuteContext(ctx); err != nil {
		color.Red("❌ Error: %v", err)
		os.Exit(1)
	}
}

// initConfig reads in config file and ENV variables
func initConfig() error {
	if cfgFile != "" {
		// Use config file from the flag
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory
		home, err := os.UserHomeDir()
		if err != nil {
			return fmt.Errorf("failed to get home directory: %w", err)
		}

		// Search config in home directory with name ".nina" (without extension)
		viper.AddConfigPath(home)
		viper.SetConfigType("yaml")
		viper.SetConfigName(".nina")
	}

	// Environment variables
	viper.SetEnvPrefix("NINA")
	viper.AutomaticEnv()

	// Set defaults - Updated for correct ports (Task #77 fix)
	viper.SetDefault("services.core-api.url", "http://localhost:13390")
	viper.SetDefault("services.memory.url", "http://localhost:13393")
	viper.SetDefault("services.graphops.url", "http://localhost:50051")
	viper.SetDefault("services.gateway.url", "http://localhost:8080")
	viper.SetDefault("services.loadtester.url", "http://localhost:13396")
	viper.SetDefault("output.format", "table")
	viper.SetDefault("output.colors", true)
	viper.SetDefault("timeouts.default", "30s")
	viper.SetDefault("timeouts.long", "300s")

	// Read config file
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("failed to read config file: %w", err)
		}
		// Config file not found is acceptable
	}

	// Set global variables from config
	if viper.IsSet("verbose") {
		verbose = viper.GetBool("verbose")
	}
	if viper.IsSet("output.format") {
		outputFormat = viper.GetString("output.format")
	}

	// Configure logging
	if verbose {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	} else {
		log.SetFlags(0)
		log.SetOutput(os.Stderr)
	}

	return nil
}

// Print banner
func init() {
	banner := color.New(color.FgMagenta, color.Bold)
	if _, err := banner.Printf(`
╔══════════════════════════════════════════════╗
║           NINAIVALAIGAL CLI TOOLS            ║
║              Developer A Task #38            ║
║        Unified Service Management CLI        ║
╚══════════════════════════════════════════════╝

`); err != nil {
		log.Printf("⚠️ Failed to print banner: %v\n", err)
	}

	// Initialize logger
	log.SetFlags(log.LstdFlags | log.Lshortfile)
}
