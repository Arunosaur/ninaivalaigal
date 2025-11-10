package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/go-resty/resty/v2"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// MemoryEntry represents a memory entry
type MemoryEntry struct {
	ID        string                 `json:"id"`
	Content   string                 `json:"content"`
	Context   string                 `json:"context"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
	Score     float64                `json:"score,omitempty"`
}

// MemoryResponse represents API response for memory operations
type MemoryResponse struct {
	Status   string        `json:"status"`
	Message  string        `json:"message"`
	Memories []MemoryEntry `json:"memories"`
	Memory   *MemoryEntry  `json:"memory,omitempty"`
	Total    int           `json:"total"`
	Page     int           `json:"page"`
	PageSize int           `json:"page_size"`
}

// createMemoryCommand creates the memory management command
func createMemoryCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "memory",
		Short: "Memory service operations",
		Long:  "Manage memories, search, and analyze memory data",
	}

	cmd.AddCommand(
		createMemoryRememberCommand(),
		createMemoryRecallCommand(),
		createMemoryListCommand(),
		createMemorySearchCommand(),
		createMemoryDeleteCommand(),
		createMemoryStatsCommand(),
		createMemoryExportCommand(),
		createMemoryImportCommand(),
		createMemorySnapshotCommand(),
		createMemoryVersionCommand(),
		createMemoryInjectionCommand(),
	)

	return cmd
}

// createMemoryRememberCommand creates a new memory
func createMemoryRememberCommand() *cobra.Command {
	var (
		content  string
		context  string
		metadata string
	)

	cmd := &cobra.Command{
		Use:   "remember [CONTENT]",
		Short: "Store a new memory",
		Long:  "Store new content in the memory service with optional context and metadata",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				content = args[0]
			}

			if content == "" {
				return fmt.Errorf("content is required")
			}

			// Parse metadata if provided
			var metadataMap map[string]interface{}
			if metadata != "" {
				if err := json.Unmarshal([]byte(metadata), &metadataMap); err != nil {
					return fmt.Errorf("invalid metadata JSON: %w", err)
				}
			}

			// Prepare request
			request := map[string]interface{}{
				"content": content,
				"context": context,
			}
			if metadataMap != nil {
				request["metadata"] = metadataMap
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetResult(&response).
				Post(baseURL + "/api/v1/memory/remember")

			if err != nil {
				return fmt.Errorf("failed to create memory: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: %s (status: %d)", response.Message, resp.StatusCode())
			}

			// Output result
			color.Green("✅ Memory stored successfully!")
			if response.Memory != nil {
				displayMemory(*response.Memory)
			}

			return nil
		},
	}

	cmd.Flags().StringVarP(&content, "content", "c", "", "Memory content")
	cmd.Flags().StringVarP(&context, "context", "x", "", "Memory context")
	cmd.Flags().StringVarP(&metadata, "metadata", "m", "", "Memory metadata (JSON)")

	return cmd
}

// createMemoryRecallCommand searches and recalls memories
func createMemoryRecallCommand() *cobra.Command {
	var (
		query     string
		limit     int
		threshold float64
		context   string
	)

	cmd := &cobra.Command{
		Use:   "recall [QUERY]",
		Short: "Search and recall memories",
		Long:  "Search for memories using semantic similarity or text matching",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) > 0 {
				query = args[0]
			}

			if query == "" {
				return fmt.Errorf("query is required")
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetQueryParams(map[string]string{
					"q":         query,
					"limit":     fmt.Sprintf("%d", limit),
					"threshold": fmt.Sprintf("%.2f", threshold),
					"context":   context,
				}).
				SetResult(&response).
				Get(baseURL + "/api/v1/memory/recall")

			if err != nil {
				return fmt.Errorf("failed to recall memories: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: %s (status: %d)", response.Message, resp.StatusCode())
			}

			// Output results
			color.Cyan("🔍 Found %d memories for query: %s", len(response.Memories), query)
			displayMemories(response.Memories)

			return nil
		},
	}

	cmd.Flags().StringVarP(&query, "query", "q", "", "Search query")
	cmd.Flags().IntVarP(&limit, "limit", "l", 10, "Maximum number of results")
	cmd.Flags().Float64VarP(&threshold, "threshold", "t", 0.7, "Similarity threshold")
	cmd.Flags().StringVarP(&context, "context", "x", "", "Filter by context")

	return cmd
}

// createMemoryListCommand lists all memories
func createMemoryListCommand() *cobra.Command {
	var (
		page     int
		pageSize int
		context  string
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List all memories",
		Long:  "List all stored memories with pagination",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetQueryParams(map[string]string{
					"page":      fmt.Sprintf("%d", page),
					"page_size": fmt.Sprintf("%d", pageSize),
					"context":   context,
				}).
				SetResult(&response).
				Get(baseURL + "/api/v1/memory/memories")

			if err != nil {
				return fmt.Errorf("failed to list memories: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: %s (status: %d)", response.Message, resp.StatusCode())
			}

			// Output results
			color.Cyan("📋 Showing page %d of memories (total: %d)", response.Page, response.Total)
			displayMemories(response.Memories)

			return nil
		},
	}

	cmd.Flags().IntVarP(&page, "page", "p", 1, "Page number")
	cmd.Flags().IntVarP(&pageSize, "page-size", "s", 20, "Page size")
	cmd.Flags().StringVarP(&context, "context", "x", "", "Filter by context")

	return cmd
}

// createMemorySearchCommand provides advanced search
func createMemorySearchCommand() *cobra.Command {
	var (
		text     string
		context  string
		metadata string
		limit    int
		sortBy   string
	)

	cmd := &cobra.Command{
		Use:   "search",
		Short: "Advanced memory search",
		Long:  "Advanced search with filters for text, context, metadata, and sorting",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Prepare search request
			request := map[string]interface{}{
				"limit":   limit,
				"sort_by": sortBy,
			}

			if text != "" {
				request["text"] = text
			}
			if context != "" {
				request["context"] = context
			}
			if metadata != "" {
				var metadataMap map[string]interface{}
				if err := json.Unmarshal([]byte(metadata), &metadataMap); err != nil {
					return fmt.Errorf("invalid metadata JSON: %w", err)
				}
				request["metadata"] = metadataMap
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetResult(&response).
				Post(baseURL + "/api/v1/memory/search")

			if err != nil {
				return fmt.Errorf("failed to search memories: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: %s (status: %d)", response.Message, resp.StatusCode())
			}

			// Output results
			color.Cyan("🔍 Found %d memories matching search criteria", len(response.Memories))
			displayMemories(response.Memories)

			return nil
		},
	}

	cmd.Flags().StringVarP(&text, "text", "t", "", "Text to search for")
	cmd.Flags().StringVarP(&context, "context", "x", "", "Context filter")
	cmd.Flags().StringVarP(&metadata, "metadata", "m", "", "Metadata filter (JSON)")
	cmd.Flags().IntVarP(&limit, "limit", "l", 20, "Maximum results")
	cmd.Flags().StringVar(&sortBy, "sort", "created_at", "Sort by field")

	return cmd
}

// createMemoryDeleteCommand deletes a memory
func createMemoryDeleteCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete [ID]",
		Short: "Delete a memory",
		Long:  "Delete a memory by ID",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			memoryID := args[0]

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetResult(&response).
				Delete(baseURL + "/api/v1/memory/delete/" + memoryID)

			if err != nil {
				return fmt.Errorf("failed to delete memory: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: %s (status: %d)", response.Message, resp.StatusCode())
			}

			color.Green("✅ Memory deleted successfully: %s", memoryID)
			return nil
		},
	}

	return cmd
}

// createMemoryStatsCommand shows memory statistics
func createMemoryStatsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "stats",
		Short: "Show memory statistics",
		Long:  "Display statistics about stored memories",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.default"))
			baseURL := viper.GetString("services.memory.url")

			var stats map[string]interface{}
			resp, err := client.R().
				SetResult(&stats).
				Get(baseURL + "/api/v1/memory/stats")

			if err != nil {
				return fmt.Errorf("failed to get memory stats: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("API error: status %d", resp.StatusCode())
			}

			// Display stats
			color.Cyan("📊 Memory Service Statistics")
			displayStats(stats)

			return nil
		},
	}

	return cmd
}

// createMemoryExportCommand exports memories
func createMemoryExportCommand() *cobra.Command {
	var (
		format    string
		output    string
		context   string
		startDate string
		endDate   string
	)

	cmd := &cobra.Command{
		Use:   "export",
		Short: "Export memories",
		Long:  "Export memories to file in various formats",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Prepare export request
			request := map[string]interface{}{
				"format": format,
			}

			if context != "" {
				request["context"] = context
			}
			if startDate != "" {
				request["start_date"] = startDate
			}
			if endDate != "" {
				request["end_date"] = endDate
			}

			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.memory.url")

			resp, err := client.R().
				SetHeader("Content-Type", "application/json").
				SetBody(request).
				SetOutput(output).
				Post(baseURL + "/api/v1/memory/export")

			if err != nil {
				return fmt.Errorf("failed to export memories: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("export failed: status %d", resp.StatusCode())
			}

			color.Green("✅ Memories exported to: %s", output)
			return nil
		},
	}

	cmd.Flags().StringVarP(&format, "format", "f", "json", "Export format (json, csv, yaml)")
	cmd.Flags().StringVarP(&output, "output", "o", "memories_export.json", "Output file")
	cmd.Flags().StringVarP(&context, "context", "x", "", "Filter by context")
	cmd.Flags().StringVar(&startDate, "start", "", "Start date (YYYY-MM-DD)")
	cmd.Flags().StringVar(&endDate, "end", "", "End date (YYYY-MM-DD)")

	return cmd
}

// createMemoryImportCommand imports memories
func createMemoryImportCommand() *cobra.Command {
	var (
		input  string
		format string
		merge  bool
	)

	cmd := &cobra.Command{
		Use:   "import",
		Short: "Import memories",
		Long:  "Import memories from file",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Make API call
			client := resty.New().SetTimeout(viper.GetDuration("timeouts.long"))
			baseURL := viper.GetString("services.memory.url")

			var response MemoryResponse
			resp, err := client.R().
				SetFile("file", input).
				SetFormData(map[string]string{
					"format": format,
					"merge":  fmt.Sprintf("%t", merge),
				}).
				SetResult(&response).
				Post(baseURL + "/api/v1/memory/import")

			if err != nil {
				return fmt.Errorf("failed to import memories: %w", err)
			}

			if resp.StatusCode() != 200 {
				return fmt.Errorf("import failed: %s (status: %d)", response.Message, resp.StatusCode())
			}

			color.Green("✅ Successfully imported memories from: %s", input)
			return nil
		},
	}

	cmd.Flags().StringVarP(&input, "input", "i", "", "Input file (required)")
	cmd.Flags().StringVarP(&format, "format", "f", "json", "Input format (json, csv, yaml)")
	cmd.Flags().BoolVar(&merge, "merge", false, "Merge with existing memories")
	if err := cmd.MarkFlagRequired("input"); err != nil {
		fmt.Printf("⚠️  Failed to mark flag required: %v\n", err)
	}

	return cmd
}

// displayMemory displays a single memory entry
func displayMemory(memory MemoryEntry) {
	fmt.Printf("\n")
	color.Cyan("ID: %s", memory.ID)
	color.White("Content: %s", memory.Content)
	if memory.Context != "" {
		color.Yellow("Context: %s", memory.Context)
	}
	if memory.Score > 0 {
		color.Green("Score: %.3f", memory.Score)
	}
	color.Magenta("Created: %s", memory.CreatedAt.Format("2006-01-02 15:04:05"))

	if len(memory.Metadata) > 0 {
		color.Blue("Metadata:")
		for k, v := range memory.Metadata {
			fmt.Printf("  %s: %v\n", k, v)
		}
	}
	fmt.Printf("\n")
}

// displayMemories displays multiple memory entries
func displayMemories(memories []MemoryEntry) {
	if len(memories) == 0 {
		color.Yellow("No memories found")
		return
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(memories, "", "  ")
		fmt.Println(string(data))
		return
	}

	// Table format
	table := tablewriter.NewWriter(color.Output)
	table.SetHeader([]string{"ID", "Content", "Context", "Score", "Created"})
	table.SetAutoWrapText(false)
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

	for _, memory := range memories {
		content := memory.Content
		if len(content) > 50 {
			content = content[:47] + "..."
		}

		score := ""
		if memory.Score > 0 {
			score = fmt.Sprintf("%.3f", memory.Score)
		}

		table.Append([]string{
			memory.ID[:8] + "...",
			content,
			memory.Context,
			score,
			memory.CreatedAt.Format("2006-01-02"),
		})
	}

	table.Render()
}

// displayStats displays statistics in a formatted way
func displayStats(stats map[string]interface{}) {
	table := tablewriter.NewWriter(color.Output)
	table.SetHeader([]string{"Metric", "Value"})
	table.SetAutoFormatHeaders(true)
	table.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
	table.SetAlignment(tablewriter.ALIGN_LEFT)

	for key, value := range stats {
		// Format key to be more readable (replace underscores with spaces, capitalize first letter)
		formattedKey := strings.ReplaceAll(key, "_", " ")
		if len(formattedKey) > 0 {
			formattedKey = strings.ToUpper(formattedKey[:1]) + formattedKey[1:]
		}
		table.Append([]string{formattedKey, fmt.Sprintf("%v", value)})
	}

	table.Render()
}
