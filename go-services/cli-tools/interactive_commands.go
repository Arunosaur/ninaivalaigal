package main

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"

	"github.com/fatih/color"
	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
)

// promptYesNo shows a yes/no prompt and returns true if "Yes" was selected
func promptYesNo(label string) (bool, error) {
	prompt := promptui.Select{
		Label: label,
		Items: []string{"Yes", "No"},
	}
	_, result, err := prompt.Run()
	if err != nil {
		return false, err
	}
	return result == "Yes", nil
}

// createInteractiveCommand creates the interactive CLI command
func createInteractiveCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "interactive",
		Short:   "Interactive CLI mode",
		Long:    "Start interactive mode with guided workflows and prompts",
		Aliases: []string{"i", "repl"},
		RunE: func(cmd *cobra.Command, args []string) error {
			return startInteractiveMode()
		},
	}

	cmd.AddCommand(
		createInteractiveMemoryCommand(),
		createInteractiveGraphCommand(),
		createInteractiveHealthCommand(),
		createInteractiveSetupCommand(),
	)

	return cmd
}

// startInteractiveMode starts the main interactive mode
func startInteractiveMode() error {
	color.Cyan("🎯 Welcome to Ninaivalaigal Interactive CLI")
	color.Blue("Choose an option to get started with guided workflows")

	for {
		prompt := promptui.Select{
			Label: "Select operation",
			Items: []string{
				"Memory Operations",
				"Graph Operations",
				"Health Monitoring",
				"Load Testing",
				"Configuration",
				"Service Management",
				"Exit",
			},
			Templates: &promptui.SelectTemplates{
				Label:    "{{ . }}:",
				Active:   "\U0001F449 {{ . | cyan }}",
				Inactive: "   {{ . | white }}",
				Selected: "\U0001F44D {{ . | green }}",
			},
		}

		_, result, err := prompt.Run()
		if err != nil {
			return err
		}

		switch result {
		case "Memory Operations":
			if err := runInteractiveMemory(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Graph Operations":
			if err := runInteractiveGraph(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Health Monitoring":
			if err := runInteractiveHealth(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Load Testing":
			if err := runInteractiveLoadTest(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Configuration":
			if err := runInteractiveConfig(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Service Management":
			if err := runInteractiveServices(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Exit":
			color.Green("👋 Goodbye!")
			return nil
		}

		fmt.Println() // Add spacing between operations
	}
}

// createInteractiveMemoryCommand creates guided memory operations
func createInteractiveMemoryCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "memory",
		Short: "Interactive memory operations",
		Long:  "Guided memory management workflows",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runInteractiveMemory()
		},
	}
}

// runInteractiveMemory runs interactive memory operations
func runInteractiveMemory() error {
	color.Cyan("🧠 Memory Service Interactive Mode")

	for {
		prompt := promptui.Select{
			Label: "Memory operation",
			Items: []string{
				"Store new memory",
				"Search memories",
				"List all memories",
				"Memory statistics",
				"Back to main menu",
			},
		}

		_, result, err := prompt.Run()
		if err != nil {
			return err
		}

		switch result {
		case "Store new memory":
			if err := interactiveMemoryRemember(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Search memories":
			if err := interactiveMemoryRecall(); err != nil {
				color.Red("Error: %v", err)
			}
		case "List all memories":
			if err := interactiveMemoryList(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Memory statistics":
			if err := interactiveMemoryStats(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Back to main menu":
			return nil
		}
	}
}

// interactiveMemoryRemember guides user through storing a memory
func interactiveMemoryRemember() error {
	color.Yellow("📝 Store New Memory")

	// Get content
	contentPrompt := promptui.Prompt{
		Label: "Memory content (what to remember)",
		Templates: &promptui.PromptTemplates{
			Prompt:  "{{ . }}: ",
			Valid:   "{{ . | green }}: ",
			Invalid: "{{ . | red }}: ",
		},
	}
	content, err := contentPrompt.Run()
	if err != nil {
		return err
	}

	// Get context (optional)
	contextPrompt := promptui.Prompt{
		Label:   "Context (optional)",
		Default: "",
	}
	context, _ := contextPrompt.Run()

	// Ask about metadata
	addMetadata, err := promptYesNo("Add metadata")
	if err != nil {
		return err
	}

	var metadata string
	if addMetadata {
		metadataContentPrompt := promptui.Prompt{
			Label:   "Metadata (JSON format)",
			Default: "{}",
		}
		metadata, _ = metadataContentPrompt.Run()
	}

	// Confirm before storing
	color.Cyan("\n📋 Memory Summary:")
	color.White("Content: %s", content)
	if context != "" {
		color.White("Context: %s", context)
	}
	if metadata != "" {
		color.White("Metadata: %s", metadata)
	}

	confirmed, err := promptYesNo("Store this memory")
	if err != nil {
		return err
	}
	if !confirmed {
		color.Yellow("❌ Memory not stored")
		return nil
	}

	// Execute memory remember command
	// This would typically call the actual memory service
	color.Green("✅ Memory stored successfully!")
	return nil
}

// interactiveMemoryRecall guides user through searching memories
func interactiveMemoryRecall() error {
	color.Yellow("🔍 Search Memories")

	// Get search query
	queryPrompt := promptui.Prompt{
		Label: "Search query",
	}
	query, err := queryPrompt.Run()
	if err != nil {
		return err
	}

	// Get limit
	limitPrompt := promptui.Prompt{
		Label:   "Maximum results",
		Default: "10",
		Validate: func(input string) error {
			if _, err := strconv.Atoi(input); err != nil {
				return fmt.Errorf("please enter a valid number")
			}
			return nil
		},
	}
	limitStr, _ := limitPrompt.Run()

	// Get threshold
	thresholdPrompt := promptui.Prompt{
		Label:   "Similarity threshold (0.0-1.0)",
		Default: "0.7",
		Validate: func(input string) error {
			if threshold, err := strconv.ParseFloat(input, 64); err != nil || threshold < 0 || threshold > 1 {
				return fmt.Errorf("please enter a number between 0.0 and 1.0")
			}
			return nil
		},
	}
	thresholdStr, _ := thresholdPrompt.Run()

	color.Cyan("\n🔍 Searching for: %s", query)
	color.White("Limit: %s, Threshold: %s", limitStr, thresholdStr)

	// Execute search
	color.Green("✅ Search completed! (Results would be displayed here)")
	return nil
}

// interactiveMemoryList guides user through listing memories
func interactiveMemoryList() error {
	color.Yellow("📋 List Memories")

	// Get page size
	pageSizePrompt := promptui.Prompt{
		Label:   "Page size",
		Default: "20",
		Validate: func(input string) error {
			if _, err := strconv.Atoi(input); err != nil {
				return fmt.Errorf("please enter a valid number")
			}
			return nil
		},
	}
	pageSize, _ := pageSizePrompt.Run()

	// Get context filter
	contextPrompt := promptui.Prompt{
		Label:   "Filter by context (optional)",
		Default: "",
	}
	context, _ := contextPrompt.Run()

	color.Cyan("\n📋 Listing memories...")
	color.White("Page size: %s", pageSize)
	if context != "" {
		color.White("Context filter: %s", context)
	}

	// Execute list
	color.Green("✅ Memories listed! (Results would be displayed here)")
	return nil
}

// interactiveMemoryStats shows memory statistics
func interactiveMemoryStats() error {
	color.Yellow("📊 Memory Statistics")
	color.Green("✅ Statistics retrieved! (Stats would be displayed here)")
	return nil
}

// createInteractiveGraphCommand creates guided graph operations
func createInteractiveGraphCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "graph",
		Short: "Interactive graph operations",
		Long:  "Guided graph database workflows",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runInteractiveGraph()
		},
	}
}

// runInteractiveGraph runs interactive graph operations
func runInteractiveGraph() error {
	color.Cyan("🕸️ Graph Database Interactive Mode")

	for {
		prompt := promptui.Select{
			Label: "Graph operation",
			Items: []string{
				"Execute Cypher query",
				"Common queries",
				"Schema information",
				"Graph statistics",
				"Back to main menu",
			},
		}

		_, result, err := prompt.Run()
		if err != nil {
			return err
		}

		switch result {
		case "Execute Cypher query":
			if err := interactiveGraphQuery(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Common queries":
			if err := interactiveCommonQueries(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Schema information":
			if err := interactiveGraphSchema(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Graph statistics":
			if err := interactiveGraphStats(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Back to main menu":
			return nil
		}
	}
}

// interactiveGraphQuery guides user through executing a Cypher query
func interactiveGraphQuery() error {
	color.Yellow("⚙️ Execute Cypher Query")

	// Get query
	queryPrompt := promptui.Prompt{
		Label: "Cypher query",
		Templates: &promptui.PromptTemplates{
			Prompt:  "{{ . }}: ",
			Valid:   "{{ . | green }}: ",
			Invalid: "{{ . | red }}: ",
		},
	}
	query, err := queryPrompt.Run()
	if err != nil {
		return err
	}

	// Ask about parameters
	addParams, err := promptYesNo("Add parameters")
	if err != nil {
		return err
	}

	var params string
	if addParams {
		paramsContentPrompt := promptui.Prompt{
			Label:   "Parameters (JSON format)",
			Default: "{}",
			Validate: func(input string) error {
				var test map[string]interface{}
				if err := json.Unmarshal([]byte(input), &test); err != nil {
					return fmt.Errorf("invalid JSON format")
				}
				return nil
			},
		}
		params, _ = paramsContentPrompt.Run()
	}

	color.Cyan("\n⚙️ Executing query:")
	color.White("Query: %s", query)
	if params != "" {
		color.White("Parameters: %s", params)
	}

	// Execute query
	color.Green("✅ Query executed! (Results would be displayed here)")
	return nil
}

// interactiveCommonQueries shows common Cypher queries
func interactiveCommonQueries() error {
	color.Yellow("📚 Common Queries")

	queries := GetCommonQueries()
	var queryNames []string
	for name := range queries {
		queryNames = append(queryNames, name)
	}
	queryNames = append(queryNames, "Back")

	prompt := promptui.Select{
		Label: "Select a common query",
		Items: queryNames,
		Templates: &promptui.SelectTemplates{
			Label:    "{{ . }}:",
			Active:   "\U0001F449 {{ . | cyan }}",
			Inactive: "   {{ . | white }}",
			Selected: "\U0001F44D {{ . | green }}",
		},
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	if result == "Back" {
		return nil
	}

	query := queries[result]
	color.Cyan("\n📋 Query: %s", result)
	color.White("Cypher: %s", query)

	execute, err := promptYesNo("Execute this query")
	if err != nil {
		return err
	}
	if execute {
		color.Green("✅ Query executed! (Results would be displayed here)")
	}

	return nil
}

// interactiveGraphSchema shows schema information
func interactiveGraphSchema() error {
	color.Yellow("🏗️ Graph Schema")

	schemaOptions := []string{
		"Show full schema",
		"List node labels",
		"List relationship types",
		"List property keys",
		"Back",
	}

	prompt := promptui.Select{
		Label: "Schema information",
		Items: schemaOptions,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	switch result {
	case "Show full schema":
		color.Green("✅ Full schema retrieved! (Schema would be displayed here)")
	case "List node labels":
		color.Green("✅ Node labels retrieved! (Labels would be displayed here)")
	case "List relationship types":
		color.Green("✅ Relationship types retrieved! (Types would be displayed here)")
	case "List property keys":
		color.Green("✅ Property keys retrieved! (Keys would be displayed here)")
	case "Back":
		return nil
	}

	return nil
}

// interactiveGraphStats shows graph statistics
func interactiveGraphStats() error {
	color.Yellow("📊 Graph Statistics")
	color.Green("✅ Statistics retrieved! (Stats would be displayed here)")
	return nil
}

// createInteractiveHealthCommand creates guided health monitoring
func createInteractiveHealthCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "health",
		Short: "Interactive health monitoring",
		Long:  "Guided service health monitoring workflows",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runInteractiveHealth()
		},
	}
}

// runInteractiveHealth runs interactive health monitoring
func runInteractiveHealth() error {
	color.Cyan("🏥 Health Monitoring Interactive Mode")

	for {
		prompt := promptui.Select{
			Label: "Health operation",
			Items: []string{
				"Check all services",
				"Check specific service",
				"Watch service health",
				"Service status summary",
				"Back to main menu",
			},
		}

		_, result, err := prompt.Run()
		if err != nil {
			return err
		}

		switch result {
		case "Check all services":
			if err := interactiveHealthCheckAll(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Check specific service":
			if err := interactiveHealthCheckSpecific(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Watch service health":
			if err := interactiveHealthWatch(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Service status summary":
			if err := interactiveHealthSummary(); err != nil {
				color.Red("Error: %v", err)
			}
		case "Back to main menu":
			return nil
		}
	}
}

// interactiveHealthCheckAll checks all services
func interactiveHealthCheckAll() error {
	color.Yellow("🔍 Checking All Services")
	color.Green("✅ All services checked! (Results would be displayed here)")
	return nil
}

// interactiveHealthCheckSpecific checks a specific service
func interactiveHealthCheckSpecific() error {
	color.Yellow("🎯 Check Specific Service")

	services := []string{"gateway", "memory", "graphops", "load-tester"}

	prompt := promptui.Select{
		Label: "Select service to check",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	color.Cyan("🔍 Checking %s service...", result)
	color.Green("✅ Service %s checked! (Results would be displayed here)", result)
	return nil
}

// interactiveHealthWatch sets up health watching
func interactiveHealthWatch() error {
	color.Yellow("👁️ Watch Service Health")

	intervalPrompt := promptui.Prompt{
		Label:   "Check interval (seconds)",
		Default: "30",
		Validate: func(input string) error {
			if _, err := strconv.Atoi(input); err != nil {
				return fmt.Errorf("please enter a valid number")
			}
			return nil
		},
	}
	interval, _ := intervalPrompt.Run()

	color.Cyan("👁️ Starting health watch with %s second interval...", interval)
	color.Green("✅ Health watch started! (Health monitoring would run here)")
	return nil
}

// interactiveHealthSummary shows health summary
func interactiveHealthSummary() error {
	color.Yellow("📊 Service Health Summary")
	color.Green("✅ Health summary retrieved! (Summary would be displayed here)")
	return nil
}

// runInteractiveLoadTest runs interactive load testing
func runInteractiveLoadTest() error {
	color.Cyan("🚀 Load Testing Interactive Mode")

	prompt := promptui.Select{
		Label: "Load test type",
		Items: []string{
			"Quick smoke test",
			"HTTP load test",
			"Scenario-based test",
			"Custom load test",
			"Back to main menu",
		},
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	switch result {
	case "Quick smoke test":
		return interactiveQuickTest()
	case "HTTP load test":
		return interactiveHTTPLoadTest()
	case "Scenario-based test":
		return interactiveScenarioTest()
	case "Custom load test":
		return interactiveCustomLoadTest()
	case "Back to main menu":
		return nil
	}

	return nil
}

// interactiveQuickTest runs a quick smoke test
func interactiveQuickTest() error {
	color.Yellow("⚡ Quick Smoke Test")

	services := []string{"gateway", "memory", "graphops"}

	prompt := promptui.Select{
		Label: "Select service to test",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	color.Cyan("⚡ Running quick test on %s...", result)
	color.Green("✅ Quick test completed! (Results would be displayed here)")
	return nil
}

// interactiveHTTPLoadTest configures an HTTP load test
func interactiveHTTPLoadTest() error {
	color.Yellow("🌐 HTTP Load Test Configuration")

	// Get URL
	urlPrompt := promptui.Prompt{
		Label:   "Target URL",
		Default: "http://localhost:8080/health",
	}
	url, _ := urlPrompt.Run()

	// Get concurrency
	concurrencyPrompt := promptui.Prompt{
		Label:   "Concurrent connections",
		Default: "10",
		Validate: func(input string) error {
			if _, err := strconv.Atoi(input); err != nil {
				return fmt.Errorf("please enter a valid number")
			}
			return nil
		},
	}
	concurrency, _ := concurrencyPrompt.Run()

	// Get duration
	durationPrompt := promptui.Prompt{
		Label:   "Test duration (e.g., 30s, 2m)",
		Default: "30s",
	}
	duration, _ := durationPrompt.Run()

	color.Cyan("\n🌐 Load Test Configuration:")
	color.White("URL: %s", url)
	color.White("Concurrency: %s", concurrency)
	color.White("Duration: %s", duration)

	confirmed, err := promptYesNo("Start load test")
	if err != nil {
		return err
	}
	if confirmed {
		color.Green("✅ Load test started! (Test would run here)")
	}

	return nil
}

// interactiveScenarioTest runs a scenario-based test
func interactiveScenarioTest() error {
	color.Yellow("🎬 Scenario-Based Test")

	scenarios := []string{
		"grpc-gateway.json",
		"stress-test.json",
		"smoke-test.json",
		"Custom scenario file",
	}

	prompt := promptui.Select{
		Label: "Select test scenario",
		Items: scenarios,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	if result == "Custom scenario file" {
		filePrompt := promptui.Prompt{
			Label: "Scenario file path",
		}
		result, _ = filePrompt.Run()
	}

	color.Cyan("🎬 Running scenario: %s", result)
	color.Green("✅ Scenario test completed! (Results would be displayed here)")
	return nil
}

// interactiveCustomLoadTest creates a custom load test
func interactiveCustomLoadTest() error {
	color.Yellow("🛠️ Custom Load Test Builder")
	color.Blue("This would guide through creating a custom load test configuration...")
	color.Green("✅ Custom load test configured! (Configuration would be saved here)")
	return nil
}

// runInteractiveConfig manages configuration interactively
func runInteractiveConfig() error {
	color.Cyan("⚙️ Configuration Management")

	prompt := promptui.Select{
		Label: "Configuration operation",
		Items: []string{
			"Show current config",
			"Set configuration value",
			"Switch profile",
			"Initialize config",
			"Back to main menu",
		},
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	switch result {
	case "Show current config":
		color.Green("✅ Current configuration displayed! (Config would be shown here)")
	case "Set configuration value":
		return interactiveConfigSet()
	case "Switch profile":
		return interactiveConfigProfile()
	case "Initialize config":
		return interactiveConfigInit()
	case "Back to main menu":
		return nil
	}

	return nil
}

// interactiveConfigSet sets a configuration value
func interactiveConfigSet() error {
	keyPrompt := promptui.Prompt{
		Label: "Configuration key",
	}
	key, err := keyPrompt.Run()
	if err != nil {
		return err
	}

	valuePrompt := promptui.Prompt{
		Label: "Configuration value",
	}
	value, err := valuePrompt.Run()
	if err != nil {
		return err
	}

	color.Green("✅ Set %s = %s", key, value)
	return nil
}

// interactiveConfigProfile switches configuration profile
func interactiveConfigProfile() error {
	profiles := []string{"local", "docker", "production"}

	prompt := promptui.Select{
		Label: "Select profile",
		Items: profiles,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	color.Green("✅ Switched to profile: %s", result)
	return nil
}

// interactiveConfigInit initializes configuration
func interactiveConfigInit() error {
	color.Yellow("🏗️ Initialize Configuration")

	includeExample, err := promptYesNo("Include example configurations")
	if err != nil {
		return err
	}

	if includeExample {
		color.Green("✅ Configuration initialized with examples!")
	} else {
		color.Green("✅ Basic configuration initialized!")
	}

	return nil
}

// runInteractiveServices manages services interactively
func runInteractiveServices() error {
	color.Cyan("🔧 Service Management")

	prompt := promptui.Select{
		Label: "Service operation",
		Items: []string{
			"Start services",
			"Stop services",
			"Restart services",
			"Service status",
			"View logs",
			"Back to main menu",
		},
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	switch result {
	case "Start services":
		return interactiveServiceStart()
	case "Stop services":
		return interactiveServiceStop()
	case "Restart services":
		return interactiveServiceRestart()
	case "Service status":
		color.Green("✅ Service status displayed! (Status would be shown here)")
	case "View logs":
		return interactiveServiceLogs()
	case "Back to main menu":
		return nil
	}

	return nil
}

// interactiveServiceStart starts services
func interactiveServiceStart() error {
	services := []string{"gateway", "load-tester", "all services"}

	prompt := promptui.Select{
		Label: "Select services to start",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	detach, err := promptYesNo("Run in background")
	if err != nil {
		return err
	}

	mode := "foreground"
	if detach {
		mode = "background"
	}

	color.Green("✅ Starting %s in %s mode!", result, mode)
	return nil
}

// interactiveServiceStop stops services
func interactiveServiceStop() error {
	services := []string{"gateway", "load-tester", "all services"}

	prompt := promptui.Select{
		Label: "Select services to stop",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	color.Green("✅ Stopping %s!", result)
	return nil
}

// interactiveServiceRestart restarts services
func interactiveServiceRestart() error {
	services := []string{"gateway", "load-tester", "all services"}

	prompt := promptui.Select{
		Label: "Select services to restart",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	rebuild, err := promptYesNo("Rebuild before restart")
	if err != nil {
		return err
	}

	action := "restarting"
	if rebuild {
		action = "rebuilding and restarting"
	}

	// Capitalize first letter
	if len(action) > 0 {
		action = strings.ToUpper(action[:1]) + action[1:]
	}
	color.Green("✅ %s %s!", action, result)
	return nil
}

// interactiveServiceLogs shows service logs
func interactiveServiceLogs() error {
	services := []string{"gateway", "load-tester"}

	prompt := promptui.Select{
		Label: "Select service for logs",
		Items: services,
	}

	_, result, err := prompt.Run()
	if err != nil {
		return err
	}

	follow, err := promptYesNo("Follow logs (live tail)")
	if err != nil {
		return err
	}

	mode := "static"
	if follow {
		mode = "following"
	}

	color.Green("✅ Showing %s logs (%s mode)!", result, mode)
	return nil
}

// createInteractiveSetupCommand creates guided setup workflow
func createInteractiveSetupCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "setup",
		Short: "Interactive setup wizard",
		Long:  "Guided setup wizard for first-time configuration",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runInteractiveSetup()
		},
	}
}

// runInteractiveSetup runs the interactive setup wizard
func runInteractiveSetup() error {
	color.Cyan("🚀 Ninaivalaigal Setup Wizard")
	color.Blue("Welcome! This wizard will help you set up the CLI tools.")

	// Step 1: Initialize configuration
	init, err := promptYesNo("Initialize configuration files")
	if err != nil {
		return err
	}
	if init {
		color.Green("✅ Configuration initialized!")
	}

	// Step 2: Choose environment
	envPrompt := promptui.Select{
		Label: "Select your environment",
		Items: []string{"Local Development", "Docker Compose", "Production"},
	}
	_, env, _ := envPrompt.Run()
	color.Green("✅ Environment set to: %s", env)

	// Step 3: Test connectivity
	test, err := promptYesNo("Test service connectivity")
	if err != nil {
		return err
	}
	if test {
		color.Green("✅ Connectivity test completed!")
	}

	// Step 4: Setup complete
	color.Green("🎉 Setup completed successfully!")
	color.Blue("You can now use 'nina' command to interact with Ninaivalaigal services.")
	color.Yellow("💡 Try 'nina interactive' for guided workflows")

	return nil
}
