package main

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/fatih/color"
	"github.com/go-resty/resty/v2"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// GraphQueryResult represents a Cypher query result
type GraphQueryResult struct {
	Columns []string                 `json:"columns"`
	Data    []map[string]interface{} `json:"data"`
	Stats   QueryStats               `json:"stats"`
}

// QueryStats represents query execution statistics
type QueryStats struct {
	NodesCreated         int `json:"nodes_created"`
	NodesDeleted         int `json:"nodes_deleted"`
	RelationshipsCreated int `json:"relationships_created"`
	RelationshipsDeleted int `json:"relationships_deleted"`
	PropertiesSet        int `json:"properties_set"`
	ExecutionTime        int `json:"execution_time_ms"`
}

// GraphResponse represents API response for graph operations
type GraphResponse struct {
	Status  string            `json:"status"`
	Message string            `json:"message"`
	Results *GraphQueryResult `json:"results,omitempty"`
	Error   string            `json:"error,omitempty"`
}

// createGraphCommand creates the graph operations command
func createGraphCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "graph",
		Short: "Graph database operations",
		Long:  "Execute Cypher queries, manage graph schema, and analyze graph data",
	}

	cmd.AddCommand(
		createGraphQueryCommand(),
		createGraphSchemaCommand(),
		createGraphStatsCommand(),
		createGraphVisualizationCommand(),
		createGraphExportCommand(),
		createGraphImportCommand(),
		createGraphBackupCommand(),
		createGraphIndexCommand(),
		createGraphConstraintsCommand(),
	)

	return cmd
}

// createGraphQueryCommand executes Cypher queries
func createGraphQueryCommand() *cobra.Command {
	var (
		query      string
		parameters string
		timeout    int
		format     string
		explain    bool
		profile    bool
	)

	cmd := &cobra.Command{
		Use:   "query [CYPHER]",
		Short: "Execute Cypher query",
		Long:  "Execute Cypher queries against the graph database with optional parameters",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				query = args[0]
			}

			if query == "" {
				// Check if it's a common query
				if commonQuery, err := cmd.Flags().GetString("common"); err == nil && commonQuery != "" {
					queries := GetCommonQueries()
					if q, exists := queries[commonQuery]; exists {
						query = q
					} else {
						return fmt.Errorf("unknown common query: %s", commonQuery)
					}
				}
			}

			if query == "" {
				return fmt.Errorf("query is required")
			}

			// Parse parameters if provided
			var params map[string]interface{}
			if parameters != "" {
				if err := json.Unmarshal([]byte(parameters), &params); err != nil {
					return fmt.Errorf("invalid parameters JSON: %w", err)
				}
			}

			// Add query prefixes for explain/profile
			if explain {
				query = "EXPLAIN " + query
			}
			if profile {
				query = "PROFILE " + query
			}

			// Prepare request
			request := map[string]interface{}{
				"query":      query,
				"parameters": params,
				"timeout_ms": timeout * 1000,
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.graphops.url")

			var response GraphResponse
			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetResult(&response).
				Post(baseURL + "/api/v1/graph/query")

			if err != nil {
				return fmt.Errorf("failed to execute query: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("query failed: %s (status: %d)", response.Message, resp.StatusCode())
			}

			if response.Error != "" {
				return fmt.Errorf("cypher error: %s", response.Error)
			}

			// Output results
			color.Cyan("🔍 Query executed successfully")
			if response.Results != nil {
				displayQueryResults(*response.Results, format)
			}

			return nil
		},
	}

	cmd.Flags().StringVarP(&query, "query", "q", "", "Cypher query")
	cmd.Flags().StringVarP(&parameters, "params", "p", "{}", "Query parameters (JSON)")
	cmd.Flags().IntVarP(&timeout, "timeout", "t", 30, "Query timeout in seconds")
	cmd.Flags().StringVarP(&format, "format", "f", "table", "Output format (table, json, csv)")
	cmd.Flags().BoolVar(&explain, "explain", false, "Add EXPLAIN to query")
	cmd.Flags().BoolVar(&profile, "profile", false, "Add PROFILE to query")
	cmd.Flags().String("common", "", "Use common query (count-nodes, node-types, etc.)")

	return cmd
}

// createGraphSchemaCommand manages graph schema
func createGraphSchemaCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "schema",
		Short: "Manage graph schema",
		Long:  "View and manage graph database schema, labels, and relationships",
	}

	// Add subcommands
	cmd.AddCommand(
		&cobra.Command{
			Use:   "show",
			Short: "Show current schema",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.schema.visualization()")
			},
		},
		&cobra.Command{
			Use:   "labels",
			Short: "Show all node labels",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.labels()")
			},
		},
		&cobra.Command{
			Use:   "relationships",
			Short: "Show all relationship types",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.relationshipTypes()")
			},
		},
		&cobra.Command{
			Use:   "properties",
			Short: "Show all property keys",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.propertyKeys()")
			},
		},
	)

	return cmd
}

// createGraphStatsCommand shows graph statistics
func createGraphStatsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "stats",
		Short: "Show graph statistics",
		Long:  "Display comprehensive statistics about the graph database",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Execute multiple queries to get comprehensive stats
			queries := map[string]string{
				"Node Count":         "MATCH (n) RETURN count(n) as count",
				"Relationship Count": "MATCH ()-[r]->() RETURN count(r) as count",
				"Node Types":         "MATCH (n) RETURN DISTINCT labels(n) as labels, count(n) as count ORDER BY count DESC",
				"Relationship Types": "MATCH ()-[r]->() RETURN DISTINCT type(r) as type, count(r) as count ORDER BY count DESC",
				"Database Info":      "CALL dbms.components()",
			}

			color.Cyan("📊 Graph Database Statistics")

			for title, query := range queries {
				fmt.Printf("\n%s:\n", color.YellowString(title))
				if err := executeStatsQuery(query); err != nil {
					color.Red("Error executing %s: %v", title, err)
				}
			}

			return nil
		},
	}

	return cmd
}

// createGraphVisualizationCommand creates graph visualizations
func createGraphVisualizationCommand() *cobra.Command {
	var (
		query  string
		output string
		format string
		limit  int
	)

	cmd := &cobra.Command{
		Use:   "visualize",
		Short: "Create graph visualizations",
		Long:  "Generate visual representations of graph data",
		RunE: func(cmd *cobra.Command, args []string) error {
			if query == "" {
				query = fmt.Sprintf("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT %d", limit)
			}

			// Prepare visualization request
			request := map[string]interface{}{
				"query":  query,
				"format": format,
				"output": output,
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.graphops.url")

			var response GraphResponse
			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetResult(&response).
				Post(baseURL + "/api/v1/graph/visualize")

			if err != nil {
				return fmt.Errorf("failed to create visualization: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("visualization failed: %s (status: %d)", response.Message, resp.StatusCode())
			}

			color.Green("✅ Visualization created: %s", output)
			return nil
		},
	}

	cmd.Flags().StringVarP(&query, "query", "q", "", "Cypher query for visualization")
	cmd.Flags().StringVarP(&output, "output", "o", "graph.png", "Output file")
	cmd.Flags().StringVarP(&format, "format", "f", "png", "Output format (png, svg, json)")
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Default query limit")

	return cmd
}

// createGraphExportCommand exports graph data
func createGraphExportCommand() *cobra.Command {
	var (
		output string
		format string
		query  string
	)

	cmd := &cobra.Command{
		Use:   "export",
		Short: "Export graph data",
		Long:  "Export graph data in various formats",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Prepare export request
			request := map[string]interface{}{
				"format": format,
			}
			if query != "" {
				request["query"] = query
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.graphops.url")

			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetOutput(output).
				Post(baseURL + "/api/v1/graph/export")

			if err != nil {
				return fmt.Errorf("failed to export graph: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("export failed: status %d", resp.StatusCode())
			}

			color.Green("✅ Graph exported to: %s", output)
			return nil
		},
	}

	cmd.Flags().StringVarP(&output, "output", "o", "graph_export.json", "Output file")
	cmd.Flags().StringVarP(&format, "format", "f", "json", "Export format (json, cypher, graphml)")
	cmd.Flags().StringVarP(&query, "query", "q", "", "Optional query to limit export")

	return cmd
}

// createGraphImportCommand imports graph data
func createGraphImportCommand() *cobra.Command {
	var (
		input  string
		format string
		merge  bool
	)

	cmd := &cobra.Command{
		Use:   "import",
		Short: "Import graph data",
		Long:  "Import graph data from file",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.graphops.url")

			var response GraphResponse
			resp, err := client.R().
				SetFile("file", input).
				SetFormData(map[string]string{
					"format": format,
					"merge":  fmt.Sprintf("%t", merge),
				}).
				SetResult(&response).
				Post(baseURL + "/api/v1/graph/import")

			if err != nil {
				return fmt.Errorf("failed to import graph: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("import failed: %s (status: %d)", response.Message, resp.StatusCode())
			}

			color.Green("✅ Successfully imported graph from: %s", input)
			return nil
		},
	}

	cmd.Flags().StringVarP(&input, "input", "i", "", "Input file (required)")
	cmd.Flags().StringVarP(&format, "format", "f", "json", "Input format (json, cypher, graphml)")
	cmd.Flags().BoolVar(&merge, "merge", false, "Merge with existing data")
	if err := cmd.MarkFlagRequired("input"); err != nil {
		fmt.Printf("⚠️  Failed to mark flag required: %v\n", err)
	}

	return cmd
}

// createGraphBackupCommand creates database backups
func createGraphBackupCommand() *cobra.Command {
	var (
		output      string
		compress    bool
		includeData bool
	)

	cmd := &cobra.Command{
		Use:   "backup",
		Short: "Create database backup",
		Long:  "Create a complete backup of the graph database",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Prepare backup request
			request := map[string]interface{}{
				"output":       output,
				"compress":     compress,
				"include_data": includeData,
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.graphops.url")

			var response GraphResponse
			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetResult(&response).
				Post(baseURL + "/api/v1/graph/backup")

			if err != nil {
				return fmt.Errorf("failed to create backup: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("backup failed: %s (status: %d)", response.Message, resp.StatusCode())
			}

			color.Green("✅ Backup created: %s", output)
			return nil
		},
	}

	cmd.Flags().StringVarP(&output, "output", "o", "graph_backup.tar.gz", "Backup file")
	cmd.Flags().BoolVar(&compress, "compress", true, "Compress backup")
	cmd.Flags().BoolVar(&includeData, "include-data", true, "Include data in backup")

	return cmd
}

// createGraphIndexCommand manages database indexes
func createGraphIndexCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "index",
		Short: "Manage database indexes",
		Long:  "Create, list, and drop database indexes",
	}

	cmd.AddCommand(
		&cobra.Command{
			Use:   "list",
			Short: "List all indexes",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.indexes()")
			},
		},
		&cobra.Command{
			Use:   "create [LABEL] [PROPERTY]",
			Short: "Create index",
			Args:  cobra.ExactArgs(2),
			RunE: func(cmd *cobra.Command, args []string) error {
				label, property := args[0], args[1]
				query := fmt.Sprintf("CREATE INDEX FOR (n:%s) ON (n.%s)", label, property)
				return executeSchemaQuery(query)
			},
		},
		&cobra.Command{
			Use:   "drop [LABEL] [PROPERTY]",
			Short: "Drop index",
			Args:  cobra.ExactArgs(2),
			RunE: func(cmd *cobra.Command, args []string) error {
				label, property := args[0], args[1]
				query := fmt.Sprintf("DROP INDEX FOR (n:%s) ON (n.%s)", label, property)
				return executeSchemaQuery(query)
			},
		},
	)

	return cmd
}

// createGraphConstraintsCommand manages database constraints
func createGraphConstraintsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "constraints",
		Short: "Manage database constraints",
		Long:  "Create, list, and drop database constraints",
	}

	cmd.AddCommand(
		&cobra.Command{
			Use:   "list",
			Short: "List all constraints",
			RunE: func(cmd *cobra.Command, args []string) error {
				return executeSchemaQuery("CALL db.constraints()")
			},
		},
		&cobra.Command{
			Use:   "unique [LABEL] [PROPERTY]",
			Short: "Create unique constraint",
			Args:  cobra.ExactArgs(2),
			RunE: func(cmd *cobra.Command, args []string) error {
				label, property := args[0], args[1]
				query := fmt.Sprintf("CREATE CONSTRAINT FOR (n:%s) REQUIRE n.%s IS UNIQUE", label, property)
				return executeSchemaQuery(query)
			},
		},
	)

	return cmd
}

// Helper functions

// executeSchemaQuery executes a schema-related query
func executeSchemaQuery(query string) error {
	// Make API call
	client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
	baseURL := viper.GetString("services.graphops.url")

	request := map[string]interface{}{
		"query": query,
	}

	var response GraphResponse
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(request).
		SetResult(&response).
		Post(baseURL + "/api/v1/graph/query")

	if err != nil {
		return fmt.Errorf("failed to execute query: %w", err)
	}

	if resp.StatusCode() != 200 {
		return fmt.Errorf("query failed: %s (status: %d)", response.Message, resp.StatusCode())
	}

	if response.Error != "" {
		return fmt.Errorf("cypher error: %s", response.Error)
	}

	// Display results
	if response.Results != nil {
		displayQueryResults(*response.Results, "table")
	}

	return nil
}

// executeStatsQuery executes a statistics query
func executeStatsQuery(query string) error {
	return executeSchemaQuery(query)
}

// displayQueryResults displays query results in the specified format
func displayQueryResults(results GraphQueryResult, format string) {
	if len(results.Data) == 0 {
		color.Yellow("No results found")
		return
	}

	switch format {
	case "json":
		data, _ := json.MarshalIndent(results, "", "  ")
		fmt.Println(string(data))
	case "csv":
		displayCSVResults(results)
	default:
		displayTableResults(results)
	}

	// Show execution stats
	if results.Stats.ExecutionTime > 0 {
		color.Magenta("\nExecution time: %dms", results.Stats.ExecutionTime)
		if results.Stats.NodesCreated > 0 {
			color.Green("Nodes created: %d", results.Stats.NodesCreated)
		}
		if results.Stats.RelationshipsCreated > 0 {
			color.Green("Relationships created: %d", results.Stats.RelationshipsCreated)
		}
		if results.Stats.PropertiesSet > 0 {
			color.Green("Properties set: %d", results.Stats.PropertiesSet)
		}
	}
}

// displayTableResults displays results in table format
func displayTableResults(results GraphQueryResult) {
	table := tablewriter.NewWriter(color.Output)
	table.SetHeader(results.Columns)
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

	for _, row := range results.Data {
		var rowData []string
		for _, col := range results.Columns {
			value := row[col]
			valueStr := fmt.Sprintf("%v", value)

			// Truncate long values
			if len(valueStr) > 50 {
				valueStr = valueStr[:47] + "..."
			}

			rowData = append(rowData, valueStr)
		}
		table.Append(rowData)
	}

	table.Render()
}

// displayCSVResults displays results in CSV format
func displayCSVResults(results GraphQueryResult) {
	// Print header
	fmt.Println(strings.Join(results.Columns, ","))

	// Print data
	for _, row := range results.Data {
		var values []string
		for _, col := range results.Columns {
			value := fmt.Sprintf("%v", row[col])
			// Escape CSV values if needed
			if strings.Contains(value, ",") || strings.Contains(value, "\"") || strings.Contains(value, "\n") {
				value = fmt.Sprintf("\"%s\"", strings.ReplaceAll(value, "\"", "\"\""))
			}
			values = append(values, value)
		}
		fmt.Println(strings.Join(values, ","))
	}
}
