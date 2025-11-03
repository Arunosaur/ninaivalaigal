package main

import (
	"testing"
)

func TestSanitizePort(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"Valid port", "8080", "8080"},
		{"Port with colon prefix", ":8080", "8080"},
		{"Empty string", "", "13395"},
		{"Whitespace only", "   ", "13395"},
		{"Whitespace with port", "  8080  ", "8080"},
		{"Port with leading colon and whitespace", "  :8080  ", "8080"},
		{"Default port", "13395", "13395"},
		{"Large port number", "65535", "65535"},
		{"Zero port", "0", "0"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := sanitizePort(tt.input)
			if result != tt.expected {
				t.Errorf("sanitizePort(%q) = %q, expected %q", tt.input, result, tt.expected)
			}
		})
	}
}
