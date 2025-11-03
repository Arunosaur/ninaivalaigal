package main

import (
	"os"
	"testing"
	"time"

	"github.com/fatih/color"
)

func TestDisplayMemory(t *testing.T) {
	memory := MemoryEntry{
		ID:        "12345678-1234-1234-1234-123456789abc",
		Content:   "Test memory content",
		Context:   "test-context",
		Metadata:  map[string]interface{}{"key": "value"},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Score:     0.95,
	}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayMemory(memory)

	w.Close()
	buf := make([]byte, 1024)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should not panic
}

func TestDisplayMemories(t *testing.T) {
	memories := []MemoryEntry{
		{
			ID:        "12345678-1234-1234-1234-123456789abc",
			Content:   "First memory",
			Context:   "test",
			CreatedAt: time.Now(),
			Score:     0.8,
		},
		{
			ID:        "87654321-4321-4321-4321-cba987654321",
			Content:   "Second memory with very long content that should be truncated",
			Context:   "test",
			CreatedAt: time.Now(),
			Score:     0.9,
		},
	}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayMemories(memories)

	w.Close()
	buf := make([]byte, 2048)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should not panic
}

func TestDisplayMemoriesEmpty(t *testing.T) {
	memories := []MemoryEntry{}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayMemories(memories)

	w.Close()
	buf := make([]byte, 1024)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should handle empty list
}

func TestDisplayMemoriesJSONFormat(t *testing.T) {
	// Set output format to JSON
	originalFormat := outputFormat
	outputFormat = "json"
	defer func() { outputFormat = originalFormat }()

	memories := []MemoryEntry{
		{
			ID:        "12345678-1234-1234-1234-123456789abc",
			Content:   "Test memory",
			Context:   "test",
			CreatedAt: time.Now(),
		},
	}

	oldStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	displayMemories(memories)

	w.Close()
	buf := make([]byte, 1024)
	r.Read(buf)
	r.Close()
	os.Stdout = oldStdout

	// Should output JSON
}

func TestDisplayStats(t *testing.T) {
	stats := map[string]interface{}{
		"total_memories":  100,
		"active_contexts": 5,
		"avg_score":       0.85,
		"last_updated":    time.Now(),
	}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayStats(stats)

	w.Close()
	buf := make([]byte, 1024)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should not panic
}

func TestDisplayStatsEmpty(t *testing.T) {
	stats := map[string]interface{}{}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayStats(stats)

	w.Close()
	buf := make([]byte, 1024)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should handle empty stats
}

func TestDisplayMemoryWithLongContent(t *testing.T) {
	longContent := make([]byte, 200)
	for i := range longContent {
		longContent[i] = 'a'
	}

	memory := MemoryEntry{
		ID:        "12345678-1234-1234-1234-123456789abc",
		Content:   string(longContent),
		Context:   "test",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	oldOutput := color.Output
	r, w, _ := os.Pipe()
	color.Output = w

	displayMemory(memory)

	w.Close()
	buf := make([]byte, 2048)
	r.Read(buf)
	r.Close()
	color.Output = oldOutput

	// Should handle long content
}
