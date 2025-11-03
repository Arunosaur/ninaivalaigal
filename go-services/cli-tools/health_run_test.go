package main

import (
	"bytes"
	"testing"
)

func TestHealthCheckRunE(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}

	checkCmd, _, _ := cmd.Find([]string{"check"})
	if checkCmd != nil {
		checkCmd.SetArgs([]string{})
		buf := new(bytes.Buffer)
		checkCmd.SetOut(buf)

		err := checkCmd.Execute()
		_ = err
	}
}

func TestHealthCheckRunEWithServices(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}

	checkCmd, _, _ := cmd.Find([]string{"check"})
	if checkCmd != nil {
		checkCmd.SetArgs([]string{"--services", "memory,gateway"})
		buf := new(bytes.Buffer)
		checkCmd.SetOut(buf)

		err := checkCmd.Execute()
		_ = err
	}
}

func TestHealthWatchRunE(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}

	watchCmd, _, _ := cmd.Find([]string{"watch"})
	if watchCmd != nil {
		// Use short timeout for testing
		watchCmd.SetArgs([]string{"--interval", "1s", "--duration", "2s"})
		buf := new(bytes.Buffer)
		watchCmd.SetOut(buf)

		err := watchCmd.Execute()
		_ = err
	}
}

func TestHealthDetailedRunE(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}

	detailedCmd, _, _ := cmd.Find([]string{"detailed"})
	if detailedCmd != nil {
		detailedCmd.SetArgs([]string{})
		buf := new(bytes.Buffer)
		detailedCmd.SetOut(buf)

		err := detailedCmd.Execute()
		_ = err
	}
}

func TestHealthSummaryRunE(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}

	summaryCmd, _, _ := cmd.Find([]string{"summary"})
	if summaryCmd != nil {
		summaryCmd.SetArgs([]string{})
		buf := new(bytes.Buffer)
		summaryCmd.SetOut(buf)

		err := summaryCmd.Execute()
		_ = err
	}
}

func TestHealthCommandsWithFlags(t *testing.T) {
	tests := []struct {
		name   string
		subCmd string
		args   []string
	}{
		{"check timeout", "check", []string{"--timeout", "5s"}},
		{"check parallel", "check", []string{"--parallel"}},
		{"check verbose", "check", []string{"--verbose"}},
		{"watch follow", "watch", []string{"--follow", "--interval", "1s", "--duration", "1s"}},
		{"detailed format", "detailed", []string{"--format", "json"}},
		{"summary format", "summary", []string{"--format", "yaml"}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := createHealthCommand()
			subCmd, _, _ := cmd.Find([]string{tt.subCmd})
			if subCmd != nil {
				subCmd.SetArgs(tt.args)
				buf := new(bytes.Buffer)
				subCmd.SetOut(buf)
				subCmd.SetErr(buf)

				err := subCmd.Execute()
				_ = err
			}
		})
	}
}

func TestHealthCheckSequentialMode(t *testing.T) {
	cmd := createHealthCommand()
	checkCmd, _, _ := cmd.Find([]string{"check"})
	if checkCmd != nil {
		checkCmd.SetArgs([]string{"--sequential"})
		buf := new(bytes.Buffer)
		checkCmd.SetOut(buf)

		err := checkCmd.Execute()
		_ = err
	}
}

func TestHealthCheckAllServices(t *testing.T) {
	cmd := createHealthCommand()
	checkCmd, _, _ := cmd.Find([]string{"check"})
	if checkCmd != nil {
		checkCmd.SetArgs([]string{"--all"})
		buf := new(bytes.Buffer)
		checkCmd.SetOut(buf)

		err := checkCmd.Execute()
		_ = err
	}
}
