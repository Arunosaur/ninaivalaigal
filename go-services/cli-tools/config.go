package main

import (
	"time"
)

// ServiceConfig holds configuration for individual services
type ServiceConfig struct {
	URL     string            `yaml:"url"`
	Timeout time.Duration     `yaml:"timeout"`
	Headers map[string]string `yaml:"headers"`
	Auth    AuthConfig        `yaml:"auth"`
}

// AuthConfig holds authentication configuration
type AuthConfig struct {
	Type   string `yaml:"type"` // bearer, basic, api-key
	Token  string `yaml:"token"`
	Key    string `yaml:"key"`
	Secret string `yaml:"secret"`
}

// OutputConfig holds output formatting configuration
type OutputConfig struct {
	Format string `yaml:"format"` // table, json, yaml
	Colors bool   `yaml:"colors"`
	Pager  bool   `yaml:"pager"`
}

// CLIConfig holds the complete CLI configuration
type CLIConfig struct {
	Services struct {
		Memory     ServiceConfig `yaml:"memory"`
		GraphOps   ServiceConfig `yaml:"graphops"`
		Gateway    ServiceConfig `yaml:"gateway"`
		LoadTester ServiceConfig `yaml:"loadtester"`
	} `yaml:"services"`

	Output   OutputConfig `yaml:"output"`
	Timeouts struct {
		Default time.Duration `yaml:"default"`
		Long    time.Duration `yaml:"long"`
	} `yaml:"timeouts"`

	Profiles map[string]ProfileConfig `yaml:"profiles"`
}

// ProfileConfig holds configuration profiles for different environments
type ProfileConfig struct {
	Name        string                   `yaml:"name"`
	Description string                   `yaml:"description"`
	Services    map[string]ServiceConfig `yaml:"services"`
	Defaults    map[string]interface{}   `yaml:"defaults"`
}

// GetDefaultProfiles returns default configuration profiles
func GetDefaultProfiles() map[string]ProfileConfig {
	return map[string]ProfileConfig{
		"local": {
			Name:        "Local Development",
			Description: "Local development environment with default ports",
			Services: map[string]ServiceConfig{
				"memory": {
					URL:     "http://localhost:8081",
					Timeout: 30 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
					},
				},
				"graphops": {
					URL:     "http://localhost:8082",
					Timeout: 60 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
					},
				},
				"gateway": {
					URL:     "http://localhost:8080",
					Timeout: 30 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
					},
				},
				"loadtester": {
					URL:     "http://localhost:8083",
					Timeout: 30 * time.Second,
				},
			},
		},
		"docker": {
			Name:        "Docker Compose",
			Description: "Docker Compose environment with service discovery",
			Services: map[string]ServiceConfig{
				"memory": {
					URL:     "http://memory-service:8081",
					Timeout: 30 * time.Second,
				},
				"graphops": {
					URL:     "http://graphops-service:8082",
					Timeout: 60 * time.Second,
				},
				"gateway": {
					URL:     "http://grpc-gateway:8080",
					Timeout: 30 * time.Second,
				},
			},
		},
		"production": {
			Name:        "Production Environment",
			Description: "Production environment with authentication and extended timeouts",
			Services: map[string]ServiceConfig{
				"memory": {
					URL:     "https://memory.ninaivalaigal.com",
					Timeout: 60 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
						"User-Agent":   "Nina-CLI/1.0",
					},
					Auth: AuthConfig{
						Type: "bearer",
					},
				},
				"graphops": {
					URL:     "https://graphops.ninaivalaigal.com",
					Timeout: 120 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
						"User-Agent":   "Nina-CLI/1.0",
					},
					Auth: AuthConfig{
						Type: "bearer",
					},
				},
				"gateway": {
					URL:     "https://api.ninaivalaigal.com",
					Timeout: 60 * time.Second,
					Headers: map[string]string{
						"Content-Type": "application/json",
						"User-Agent":   "Nina-CLI/1.0",
					},
					Auth: AuthConfig{
						Type: "bearer",
					},
				},
			},
		},
	}
}

// GetMemoryTargets returns predefined memory service endpoints
func GetMemoryTargets() map[string]string {
	return map[string]string{
		"remember":    "/api/v1/memory/remember",
		"recall":      "/api/v1/memory/recall",
		"memories":    "/api/v1/memory/memories",
		"search":      "/api/v1/memory/search",
		"delete":      "/api/v1/memory/delete",
		"update":      "/api/v1/memory/update",
		"stats":       "/api/v1/memory/stats",
		"health":      "/api/v1/memory/health",
		"collections": "/api/v1/memory/collections",
		"export":      "/api/v1/memory/export",
		"import":      "/api/v1/memory/import",
	}
}

// GetGraphTargets returns predefined graph service endpoints
func GetGraphTargets() map[string]string {
	return map[string]string{
		"query":       "/api/v1/graph/query",
		"transaction": "/api/v1/graph/transaction",
		"schema":      "/api/v1/graph/schema",
		"indexes":     "/api/v1/graph/indexes",
		"constraints": "/api/v1/graph/constraints",
		"stats":       "/api/v1/graph/stats",
		"health":      "/api/v1/graph/health",
		"backup":      "/api/v1/graph/backup",
		"restore":     "/api/v1/graph/restore",
		"export":      "/api/v1/graph/export",
		"import":      "/api/v1/graph/import",
		"visualize":   "/api/v1/graph/visualize",
	}
}

// GetCommonQueries returns frequently used Cypher queries
func GetCommonQueries() map[string]string {
	return map[string]string{
		"count-nodes":       "MATCH (n) RETURN count(n) as total_nodes",
		"count-relations":   "MATCH ()-[r]->() RETURN count(r) as total_relations",
		"node-types":        "MATCH (n) RETURN DISTINCT labels(n) as node_types, count(n) as count ORDER BY count DESC",
		"relation-types":    "MATCH ()-[r]->() RETURN DISTINCT type(r) as relation_type, count(r) as count ORDER BY count DESC",
		"memory-nodes":      "MATCH (m:Memory) RETURN m LIMIT 10",
		"recent-memories":   "MATCH (m:Memory) RETURN m ORDER BY m.created_at DESC LIMIT 10",
		"memory-search":     "MATCH (m:Memory) WHERE m.content CONTAINS $query RETURN m LIMIT 20",
		"memory-by-context": "MATCH (m:Memory) WHERE m.context = $context RETURN m",
		"orphaned-nodes":    "MATCH (n) WHERE NOT (n)-[]->() AND NOT ()-[]->(n) RETURN n",
		"popular-memories":  "MATCH (m:Memory)-[r]->() RETURN m, count(r) as connections ORDER BY connections DESC LIMIT 10",
		"graph-structure":   "MATCH (n)-[r]->(m) RETURN labels(n)[0] as source, type(r) as relation, labels(m)[0] as target, count(*) as count",
		"database-info":     "CALL db.info() YIELD *",
		"performance-stats": "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Page cache') YIELD attributes",
	}
}

// GetLoadTestProfiles returns predefined load testing profiles
func GetLoadTestProfiles() map[string]interface{} {
	return map[string]interface{}{
		"smoke": map[string]interface{}{
			"concurrency": 1,
			"requests":    10,
			"duration":    "30s",
			"ramp_up":     "5s",
			"description": "Basic smoke test to verify service availability",
		},
		"light": map[string]interface{}{
			"concurrency": 10,
			"requests":    100,
			"duration":    "60s",
			"ramp_up":     "10s",
			"description": "Light load test for basic performance validation",
		},
		"moderate": map[string]interface{}{
			"concurrency": 50,
			"requests":    1000,
			"duration":    "300s",
			"ramp_up":     "30s",
			"description": "Moderate load test for normal usage patterns",
		},
		"heavy": map[string]interface{}{
			"concurrency": 200,
			"requests":    10000,
			"duration":    "600s",
			"ramp_up":     "60s",
			"description": "Heavy load test for high-traffic scenarios",
		},
		"stress": map[string]interface{}{
			"concurrency": 500,
			"requests":    50000,
			"duration":    "1800s",
			"ramp_up":     "120s",
			"description": "Stress test to find breaking points",
		},
		"endurance": map[string]interface{}{
			"concurrency": 100,
			"requests":    -1, // Unlimited
			"duration":    "3600s",
			"ramp_up":     "300s",
			"description": "Endurance test for long-running stability",
		},
	}
}
