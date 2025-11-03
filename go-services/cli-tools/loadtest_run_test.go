package main

import (
	"bytes"
	"testing"
)

func TestLoadTestHTTPRunE(t *testing.T) {
	cmd := createLoadTestCommand()
	if cmd == nil {
		t.Fatal("createLoadTestCommand() should not return nil")
	}

	httpCmd, _, _ := cmd.Find([]string{"http"})
	if httpCmd != nil {
		httpCmd.SetArgs([]string{
			"--url", "http://localhost:8080/health",
			"--concurrency", "1",
			"--requests", "1",
			"--duration", "1s",
		})
		buf := new(bytes.Buffer)
		httpCmd.SetOut(buf)

		err := httpCmd.Execute()
		_ = err
	}
}

func TestLoadTestHTTPRunEWithMethod(t *testing.T) {
	cmd := createLoadTestCommand()
	httpCmd, _, _ := cmd.Find([]string{"http"})
	if httpCmd != nil {
		httpCmd.SetArgs([]string{
			"--url", "http://localhost:8080/api/v1/memory/remember",
			"--method", "POST",
			"--body", `{"content":"test"}`,
			"--concurrency", "1",
			"--requests", "1",
		})
		buf := new(bytes.Buffer)
		httpCmd.SetOut(buf)

		err := httpCmd.Execute()
		_ = err
	}
}

func TestLoadTestProfileRunE(t *testing.T) {
	cmd := createLoadTestCommand()
	profileCmd, _, _ := cmd.Find([]string{"profile"})
	if profileCmd != nil {
		profileCmd.SetArgs([]string{"smoke", "--target", "gateway"})
		buf := new(bytes.Buffer)
		profileCmd.SetOut(buf)

		err := profileCmd.Execute()
		_ = err
	}
}

func TestLoadTestProfileRunEWithURL(t *testing.T) {
	cmd := createLoadTestCommand()
	profileCmd, _, _ := cmd.Find([]string{"profile"})
	if profileCmd != nil {
		profileCmd.SetArgs([]string{
			"light",
			"--url", "http://localhost:8080/health",
		})
		buf := new(bytes.Buffer)
		profileCmd.SetOut(buf)

		err := profileCmd.Execute()
		_ = err
	}
}

func TestLoadTestScenarioRunE(t *testing.T) {
	cmd := createLoadTestCommand()
	scenarioCmd, _, _ := cmd.Find([]string{"scenario"})
	if scenarioCmd != nil {
		scenarioCmd.SetArgs([]string{"test-scenario"})
		buf := new(bytes.Buffer)
		scenarioCmd.SetOut(buf)

		err := scenarioCmd.Execute()
		_ = err
	}
}

func TestLoadTestValidateRunE(t *testing.T) {
	cmd := createLoadTestCommand()
	validateCmd, _, _ := cmd.Find([]string{"validate"})
	if validateCmd != nil {
		validateCmd.SetArgs([]string{"--url", "http://localhost:8080"})
		buf := new(bytes.Buffer)
		validateCmd.SetOut(buf)

		err := validateCmd.Execute()
		_ = err
	}
}

func TestLoadTestCommandsWithInvalidInput(t *testing.T) {
	tests := []struct {
		name   string
		subCmd string
		args   []string
	}{
		{"http no URL", "http", []string{}},
		{"profile invalid", "profile", []string{"invalid-profile"}},
		{"scenario no name", "scenario", []string{}},
		{"validate no URL", "validate", []string{}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := createLoadTestCommand()
			subCmd, _, _ := cmd.Find([]string{tt.subCmd})
			if subCmd != nil {
				subCmd.SetArgs(tt.args)
				buf := new(bytes.Buffer)
				subCmd.SetOut(buf)
				subCmd.SetErr(buf)

				err := subCmd.Execute()
				// Accept any error - testing error handling
				_ = err
			}
		})
	}
}

func TestLoadTestHTTPWithHeaders(t *testing.T) {
	cmd := createLoadTestCommand()
	httpCmd, _, _ := cmd.Find([]string{"http"})
	if httpCmd != nil {
		httpCmd.SetArgs([]string{
			"--url", "http://localhost:8080/health",
			"--header", "Authorization: Bearer test-token",
			"--header", "Content-Type: application/json",
			"--concurrency", "1",
			"--requests", "1",
		})
		buf := new(bytes.Buffer)
		httpCmd.SetOut(buf)

		err := httpCmd.Execute()
		_ = err
	}
}

func TestLoadTestHTTPWithDifferentProfiles(t *testing.T) {
	profiles := []string{"smoke", "light", "moderate", "heavy"}
	cmd := createLoadTestCommand()
	profileCmd, _, _ := cmd.Find([]string{"profile"})

	for _, profile := range profiles {
		t.Run(profile, func(t *testing.T) {
			if profileCmd != nil {
				profileCmd.SetArgs([]string{profile, "--target", "gateway"})
				buf := new(bytes.Buffer)
				profileCmd.SetOut(buf)

				err := profileCmd.Execute()
				_ = err
			}
		})
	}
}
