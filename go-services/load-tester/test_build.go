// Quick build test to verify all files compile together
package main

import (
	"fmt"
	"runtime"
)

// BuildTest validates that all components are properly integrated
func BuildTest() {
	fmt.Printf("Build Test - Go Load Tester v%s\n", Version)
	fmt.Printf("Runtime: %s %s\n", runtime.GOOS, runtime.GOARCH)

	// Test config creation
	config := NewLoadTestConfig()
	fmt.Printf("Default config URL: %s\n", config.URL)

	// Test profiles
	profiles := GetDefaultProfiles()
	fmt.Printf("Available profiles: %d\n", len(profiles))

	// Test targets
	targets := GetNinaivalaigalTargets()
	fmt.Printf("Ninaivalaigal targets: %d\n", len(targets))

	fmt.Println("✅ Build test passed - all components integrated successfully")
}
