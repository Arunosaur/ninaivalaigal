package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/fatih/color"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"gopkg.in/yaml.v3"
)

// createConfigCommand creates the configuration management command
func createConfigCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Configuration management",
		Long:  "Manage CLI configuration, profiles, and service settings",
	}

	cmd.AddCommand(
		createConfigShowCommand(),
		createConfigSetCommand(),
		createConfigGetCommand(),
		createConfigInitCommand(),
		createConfigProfileCommand(),
		createConfigValidateCommand(),
		createConfigExportCommand(),
		createConfigImportCommand(),
	)

	return cmd
}

// createConfigShowCommand shows current configuration
func createConfigShowCommand() *cobra.Command {
	var (
		format string
		all    bool
	)

	cmd := &cobra.Command{
		Use:   "show [KEY]",
		Short: "Show configuration",
		Long:  "Display current configuration settings",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var key string
			if len(args) > 0 {
				key = args[0]
			}

			if key != "" {
				// Show specific key
				value := viper.Get(key)
				if value == nil {
					return fmt.Errorf("configuration key not found: %s", key)
				}

				switch format {
				case "json":
					data, _ := json.MarshalIndent(value, "", "  ")
					fmt.Println(string(data))
				case "yaml":
					data, _ := yaml.Marshal(value)
					fmt.Print(string(data))
				default:
					fmt.Printf("%s: %v\n", key, value)
				}
			} else {
				// Show all configuration
				settings := viper.AllSettings()

				switch format {
				case "json":
					data, _ := json.MarshalIndent(settings, "", "  ")
					fmt.Println(string(data))
				case "yaml":
					data, _ := yaml.Marshal(settings)
					fmt.Print(string(data))
				default:
					displayConfigTable(settings, all)
				}
			}

			return nil
		},
	}

	cmd.Flags().StringVarP(&format, "format", "f", "table", "Output format (table, json, yaml)")
	cmd.Flags().BoolVarP(&all, "all", "a", false, "Show all settings including defaults")

	return cmd
}

// createConfigSetCommand sets configuration values
func createConfigSetCommand() *cobra.Command {
	var (
		global  bool
		profile string
	)

	cmd := &cobra.Command{
		Use:   "set [KEY] [VALUE]",
		Short: "Set configuration value",
		Long:  "Set a configuration key to a specific value",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			key, value := args[0], args[1]

			// Try to parse value as JSON for complex types
			var parsedValue interface{}
			if err := json.Unmarshal([]byte(value), &parsedValue); err != nil {
				// If not JSON, treat as string
				parsedValue = value
			}

			// Set in viper
			viper.Set(key, parsedValue)

			// Save to config file if global flag is set
			if global {
				if err := saveConfig(); err != nil {
					return fmt.Errorf("failed to save configuration: %w", err)
				}
				color.Green("✅ Configuration saved globally")
			} else {
				color.Green("✅ Configuration set (session only)")
				color.Yellow("💡 Use --global to persist changes")
			}

			color.Cyan("Set %s = %v", key, parsedValue)
			return nil
		},
	}

	cmd.Flags().BoolVar(&global, "global", false, "Save to global configuration file")
	cmd.Flags().StringVar(&profile, "profile", "", "Set for specific profile")

	return cmd
}

// createConfigGetCommand gets configuration values
func createConfigGetCommand() *cobra.Command {
	var defaultValue string

	cmd := &cobra.Command{
		Use:   "get [KEY]",
		Short: "Get configuration value",
		Long:  "Get the value of a configuration key",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			key := args[0]

			value := viper.Get(key)
			if value == nil {
				if defaultValue != "" {
					fmt.Println(defaultValue)
				} else {
					return fmt.Errorf("configuration key not found: %s", key)
				}
			} else {
				fmt.Printf("%v\n", value)
			}

			return nil
		},
	}

	cmd.Flags().StringVar(&defaultValue, "default", "", "Default value if key not found")

	return cmd
}

// createConfigInitCommand initializes configuration
func createConfigInitCommand() *cobra.Command {
	var (
		force   bool
		profile string
		example bool
	)

	cmd := &cobra.Command{
		Use:   "init",
		Short: "Initialize configuration",
		Long:  "Create initial configuration file with default settings",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Get config file path
			configPath := viper.ConfigFileUsed()
			if configPath == "" {
				home, _ := os.UserHomeDir()
				configPath = filepath.Join(home, ".nina.yaml")
			}

			// Check if config exists
			if _, err := os.Stat(configPath); err == nil && !force {
				return fmt.Errorf("configuration file already exists: %s (use --force to overwrite)", configPath)
			}

			// Create config structure
			config := createDefaultConfig()

			// Add example settings if requested
			if example {
				config = addExampleConfig(config)
			}

			// Write config file
			data, err := yaml.Marshal(config)
			if err != nil {
				return fmt.Errorf("failed to marshal configuration: %w", err)
			}

			if err := os.WriteFile(configPath, data, 0644); err != nil {
				return fmt.Errorf("failed to write configuration file: %w", err)
			}

			color.Green("✅ Configuration initialized: %s", configPath)

			if example {
				color.Blue("📖 Example configuration with all options has been created")
				color.Yellow("💡 Edit the file to customize your settings")
			}

			return nil
		},
	}

	cmd.Flags().BoolVar(&force, "force", false, "Overwrite existing configuration")
	cmd.Flags().StringVar(&profile, "profile", "local", "Initial profile to create")
	cmd.Flags().BoolVar(&example, "example", false, "Include example configurations")

	return cmd
}

// createConfigProfileCommand manages configuration profiles
func createConfigProfileCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "profile",
		Short: "Manage configuration profiles",
		Long:  "Create, list, and switch between configuration profiles",
	}

	cmd.AddCommand(
		&cobra.Command{
			Use:   "list",
			Short: "List available profiles",
			RunE: func(cmd *cobra.Command, args []string) error {
				profiles := GetDefaultProfiles()

				color.Cyan("📋 Available Profiles:")
				table := tablewriter.NewWriter(color.Output)
				table.SetHeader([]string{"Profile", "Description", "Services"})
				table.SetAutoFormatHeaders(true)
				table.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
				table.SetAlignment(tablewriter.ALIGN_LEFT)

				for name, profile := range profiles {
					serviceNames := make([]string, 0, len(profile.Services))
					for serviceName := range profile.Services {
						serviceNames = append(serviceNames, serviceName)
					}

					table.Append([]string{
						name,
						profile.Description,
						strings.Join(serviceNames, ", "),
					})
				}

				table.Render()
				return nil
			},
		},
		&cobra.Command{
			Use:   "show [PROFILE]",
			Short: "Show profile configuration",
			Args:  cobra.ExactArgs(1),
			RunE: func(cmd *cobra.Command, args []string) error {
				profileName := args[0]
				profiles := GetDefaultProfiles()

				profile, exists := profiles[profileName]
				if !exists {
					return fmt.Errorf("profile not found: %s", profileName)
				}

				color.Cyan("📋 Profile: %s", profileName)
				color.White("Description: %s", profile.Description)

				fmt.Printf("\n%s Services:\n", color.BlueString("🔧"))
				for serviceName, serviceConfig := range profile.Services {
					color.Yellow("  %s:", serviceName)
					fmt.Printf("    URL: %s\n", serviceConfig.URL)
					fmt.Printf("    Timeout: %s\n", serviceConfig.Timeout)
					if len(serviceConfig.Headers) > 0 {
						fmt.Printf("    Headers: %v\n", serviceConfig.Headers)
					}
				}

				return nil
			},
		},
		&cobra.Command{
			Use:   "use [PROFILE]",
			Short: "Switch to profile",
			Args:  cobra.ExactArgs(1),
			RunE: func(cmd *cobra.Command, args []string) error {
				profileName := args[0]
				profiles := GetDefaultProfiles()

				profile, exists := profiles[profileName]
				if !exists {
					return fmt.Errorf("profile not found: %s", profileName)
				}

				// Apply profile settings
				for serviceName, serviceConfig := range profile.Services {
					viper.Set(fmt.Sprintf("services.%s.url", serviceName), serviceConfig.URL)
					viper.Set(fmt.Sprintf("services.%s.timeout", serviceName), serviceConfig.Timeout)
					if len(serviceConfig.Headers) > 0 {
						viper.Set(fmt.Sprintf("services.%s.headers", serviceName), serviceConfig.Headers)
					}
				}

				viper.Set("current_profile", profileName)

				color.Green("✅ Switched to profile: %s", profileName)
				color.Blue("📋 %s", profile.Description)

				return nil
			},
		},
	)

	return cmd
}

// createConfigValidateCommand validates configuration
func createConfigValidateCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "validate",
		Short: "Validate configuration",
		Long:  "Validate current configuration for correctness and completeness",
		RunE: func(cmd *cobra.Command, args []string) error {
			color.Cyan("🔍 Validating configuration...")

			errors := validateConfiguration()

			if len(errors) == 0 {
				color.Green("✅ Configuration is valid")
				return nil
			}

			color.Red("❌ Configuration validation failed:")
			for _, err := range errors {
				color.Red("  • %s", err)
			}

			return fmt.Errorf("configuration validation failed with %d errors", len(errors))
		},
	}

	return cmd
}

// createConfigExportCommand exports configuration
func createConfigExportCommand() *cobra.Command {
	var (
		output string
		format string
	)

	cmd := &cobra.Command{
		Use:   "export",
		Short: "Export configuration",
		Long:  "Export current configuration to file",
		RunE: func(cmd *cobra.Command, args []string) error {
			settings := viper.AllSettings()

			var data []byte
			var err error

			switch format {
			case "json":
				data, err = json.MarshalIndent(settings, "", "  ")
			case "yaml":
				data, err = yaml.Marshal(settings)
			default:
				return fmt.Errorf("unsupported format: %s", format)
			}

			if err != nil {
				return fmt.Errorf("failed to marshal configuration: %w", err)
			}

			if err := os.WriteFile(output, data, 0644); err != nil {
				return fmt.Errorf("failed to write file: %w", err)
			}

			color.Green("✅ Configuration exported to: %s", output)
			return nil
		},
	}

	cmd.Flags().StringVarP(&output, "output", "o", "nina-config.yaml", "Output file")
	cmd.Flags().StringVarP(&format, "format", "f", "yaml", "Output format (yaml, json)")

	return cmd
}

// createConfigImportCommand imports configuration
func createConfigImportCommand() *cobra.Command {
	var (
		input string
		merge bool
	)

	cmd := &cobra.Command{
		Use:   "import",
		Short: "Import configuration",
		Long:  "Import configuration from file",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Read file
			data, err := os.ReadFile(input)
			if err != nil {
				return fmt.Errorf("failed to read file: %w", err)
			}

			// Parse based on file extension
			var config map[string]interface{}
			ext := filepath.Ext(input)

			switch ext {
			case ".json":
				err = json.Unmarshal(data, &config)
			case ".yaml", ".yml":
				err = yaml.Unmarshal(data, &config)
			default:
				return fmt.Errorf("unsupported file format: %s", ext)
			}

			if err != nil {
				return fmt.Errorf("failed to parse configuration: %w", err)
			}

			// Apply configuration
			if merge {
				// Merge with existing config
				for key, value := range config {
					viper.Set(key, value)
				}
			} else {
				// Replace entire config
				for key := range viper.AllSettings() {
					viper.Set(key, nil)
				}
				for key, value := range config {
					viper.Set(key, value)
				}
			}

			// Save configuration
			if err := saveConfig(); err != nil {
				return fmt.Errorf("failed to save configuration: %w", err)
			}

			color.Green("✅ Configuration imported from: %s", input)
			return nil
		},
	}

	cmd.Flags().StringVarP(&input, "input", "i", "", "Input file (required)")
	cmd.Flags().BoolVar(&merge, "merge", false, "Merge with existing configuration")
	if err := cmd.MarkFlagRequired("input"); err != nil {
		fmt.Printf("⚠️  Failed to mark flag required: %v\n", err)
	}

	return cmd
}

// Helper functions

// displayConfigTable displays configuration in table format
func displayConfigTable(settings map[string]interface{}, showAll bool) {
	color.Cyan("🔧 Current Configuration")

	// Current profile
	if profile := viper.GetString("current_profile"); profile != "" {
		color.Yellow("Active Profile: %s", profile)
	}

	// Configuration file
	if configFile := viper.ConfigFileUsed(); configFile != "" {
		color.Blue("Config File: %s", configFile)
	}

	fmt.Printf("\n")

	// Create table
	table := tablewriter.NewWriter(color.Output)
	table.SetHeader([]string{"Key", "Value", "Source"})
	table.SetAutoFormatHeaders(true)
	table.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
	table.SetAlignment(tablewriter.ALIGN_LEFT)
	table.SetAutoWrapText(false)

	// Add settings to table
	addSettingsToTable(table, settings, "", showAll)

	table.Render()
}

// addSettingsToTable recursively adds settings to table
func addSettingsToTable(table *tablewriter.Table, settings map[string]interface{}, prefix string, showAll bool) {
	for key, value := range settings {
		fullKey := key
		if prefix != "" {
			fullKey = prefix + "." + key
		}

		// Skip some internal keys unless showing all
		if !showAll && isInternalKey(fullKey) {
			continue
		}

		switch v := value.(type) {
		case map[string]interface{}:
			// Nested object - recurse
			addSettingsToTable(table, v, fullKey, showAll)
		default:
			// Simple value
			valueStr := fmt.Sprintf("%v", v)
			if len(valueStr) > 50 {
				valueStr = valueStr[:47] + "..."
			}

			source := "default"
			if viper.InConfig(fullKey) {
				source = "config"
			}
			if os.Getenv("NINA_"+strings.ToUpper(strings.ReplaceAll(fullKey, ".", "_"))) != "" {
				source = "env"
			}

			table.Append([]string{fullKey, valueStr, source})
		}
	}
}

// isInternalKey checks if a key is internal and should be hidden by default
func isInternalKey(key string) bool {
	internalKeys := []string{
		"current_profile",
	}

	for _, internal := range internalKeys {
		if strings.HasPrefix(key, internal) {
			return true
		}
	}

	return false
}

// createDefaultConfig creates default configuration structure
func createDefaultConfig() map[string]interface{} {
	return map[string]interface{}{
		"services": map[string]interface{}{
			"memory": map[string]interface{}{
				"url":     "http://localhost:8081",
				"timeout": "30s",
			},
			"graphops": map[string]interface{}{
				"url":     "http://localhost:8082",
				"timeout": "60s",
			},
			"gateway": map[string]interface{}{
				"url":     "http://localhost:8080",
				"timeout": "30s",
			},
		},
		"output": map[string]interface{}{
			"format": "table",
			"colors": true,
		},
		"timeouts": map[string]interface{}{
			"default": "30s",
			"long":    "300s",
		},
	}
}

// addExampleConfig adds example configuration options
func addExampleConfig(config map[string]interface{}) map[string]interface{} {
	// Add authentication examples
	if services, ok := config["services"].(map[string]interface{}); ok {
		for serviceName, serviceConfig := range services {
			if sc, ok := serviceConfig.(map[string]interface{}); ok {
				sc["headers"] = map[string]string{
					"User-Agent": "Nina-CLI/1.0",
				}
				sc["auth"] = map[string]interface{}{
					"type":  "bearer",
					"token": "your-token-here",
				}
				services[serviceName] = sc
			}
		}
	}

	// Add profiles
	config["profiles"] = GetDefaultProfiles()

	return config
}

// validateConfiguration validates the current configuration
func validateConfiguration() []string {
	var errors []string

	// Check required service URLs
	services := []string{"memory", "graphops", "gateway"}
	for _, service := range services {
		url := viper.GetString(fmt.Sprintf("services.%s.url", service))
		if url == "" {
			errors = append(errors, fmt.Sprintf("missing URL for service: %s", service))
		}
	}

	// Check output format
	outputFormat := viper.GetString("output.format")
	validFormats := []string{"table", "json", "yaml"}
	isValidFormat := false
	for _, format := range validFormats {
		if outputFormat == format {
			isValidFormat = true
			break
		}
	}
	if !isValidFormat {
		errors = append(errors, fmt.Sprintf("invalid output format: %s (valid: %s)",
			outputFormat, strings.Join(validFormats, ", ")))
	}

	return errors
}

// saveConfig saves current configuration to file
func saveConfig() error {
	configPath := viper.ConfigFileUsed()
	if configPath == "" {
		home, _ := os.UserHomeDir()
		configPath = filepath.Join(home, ".nina.yaml")
	}

	return viper.WriteConfigAs(configPath)
}
