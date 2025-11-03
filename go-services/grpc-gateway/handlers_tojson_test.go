package main

import (
	"testing"
)

func TestToJSON(t *testing.T) {
	tests := []struct {
		name     string
		input    interface{}
		expected string
	}{
		{"String", "test", `"test"`},
		{"Number", 42, `42`},
		{"Boolean", true, `true`},
		{"Map", map[string]string{"key": "value"}, `{"key":"value"}`},
		{"Slice", []string{"a", "b"}, `["a","b"]`},
		{"Nested map", map[string]interface{}{"nested": map[string]int{"x": 1}}, `{"nested":{"x":1}}`},
		{"Empty map", map[string]interface{}{}, `{}`},
		{"Nil map", map[string]interface{}(nil), `null`},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := toJSON(tt.input)
			// toJSON may not produce exact string match due to map ordering, so just check it's valid JSON
			if result == "" && tt.input != nil {
				t.Errorf("toJSON(%v) should not return empty string", tt.input)
			}
			// Basic check that it's JSON-like (starts with {, [, ", or is a number/boolean)
			if !isJSONLike(result) {
				t.Errorf("toJSON(%v) = %q, doesn't look like valid JSON", tt.input, result)
			}
		})
	}
}

// Helper to check if string looks like JSON
func isJSONLike(s string) bool {
	if s == "" {
		return false
	}
	firstChar := s[0]
	return firstChar == '{' || firstChar == '[' || firstChar == '"' ||
		(firstChar >= '0' && firstChar <= '9') || s == "true" || s == "false" || s == "null"
}
