-- SPDX-License-Identifier: Proprietary
-- Copyright (c) 2025 Medhasys LLC
--
-- wrk Load Testing Script for GraphOps gRPC Service
-- SPEC-099 Phase 1: Throughput Benchmarking

-- Configuration
local queries = {
    -- Simple match (warm path, should be fast)
    {
        name = "simple_match",
        cypher = "MATCH (n:User) RETURN n LIMIT 10",
        weight = 0.4  -- 40% of requests
    },
    -- Graph traversal (more complex, tests indexes)
    {
        name = "graph_traversal",
        cypher = "MATCH (u:User)-[:CREATED]->(m:Memory) RETURN u.name, count(m) as memory_count",
        weight = 0.4  -- 40% of requests
    },
    -- Deep traversal (stress test)
    {
        name = "deep_traversal",
        cypher = "MATCH path = (u:User)-[:CREATED*1..3]->(m:Memory) RETURN path LIMIT 20",
        weight = 0.2  -- 20% of requests
    }
}

-- Calculate cumulative weights for selection
local cumulative_weights = {}
local total = 0
for i, q in ipairs(queries) do
    total = total + q.weight
    cumulative_weights[i] = total
end

-- Thread setup
function setup(thread)
    thread:set("id", counter)
    counter = counter + 1
end

-- Initialize counters
counter = 1
requests = 0
responses = 0

-- Request generation
function request()
    -- Select query based on weighted random
    local rand = math.random()
    local selected_query = queries[1]

    for i, weight in ipairs(cumulative_weights) do
        if rand <= weight / total then
            selected_query = queries[i]
            break
        end
    end

    -- Build gRPC request (adjust based on your HTTP/gRPC bridge)
    -- For HTTP-based testing:
    local body = string.format([[{
        "query": %q,
        "parameters": {},
        "timeout_ms": 5000,
        "trace_id": "wrk-%d"
    }]], selected_query.cypher, requests)

    requests = requests + 1

    -- Return HTTP request
    return wrk.format("POST", "/graphops/execute",
        {
            ["Content-Type"] = "application/json",
            ["Accept"] = "application/json"
        },
        body
    )
end

-- Response handling
function response(status, headers, body)
    responses = responses + 1

    -- Track errors
    if status ~= 200 then
        print(string.format("Error: HTTP %d - %s", status, body))
    end
end

-- Results summary
function done(summary, latency, requests)
    io.write("\n")
    io.write("="..string.rep("=", 60).."\n")
    io.write("  GraphOps Load Test Results\n")
    io.write("="..string.rep("=", 60).."\n")
    io.write(string.format("  Duration:        %d ms\n", summary.duration / 1000))
    io.write(string.format("  Requests:        %d\n", summary.requests))
    io.write(string.format("  Throughput:      %.2f req/s\n", summary.requests / (summary.duration / 1000000)))
    io.write(string.format("  Avg Latency:     %.2f ms\n", latency.mean / 1000))
    io.write(string.format("  P50 Latency:     %.2f ms\n", latency:percentile(50) / 1000))
    io.write(string.format("  P95 Latency:     %.2f ms\n", latency:percentile(95) / 1000))
    io.write(string.format("  P99 Latency:     %.2f ms\n", latency:percentile(99) / 1000))
    io.write(string.format("  Max Latency:     %.2f ms\n", latency.max / 1000))
    io.write(string.format("  Errors:          %d (%.2f%%)\n",
        summary.errors.connect + summary.errors.read + summary.errors.write + summary.errors.timeout,
        (summary.errors.connect + summary.errors.read + summary.errors.write + summary.errors.timeout) / summary.requests * 100
    ))
    io.write("="..string.rep("=", 60).."\n")

    -- Query distribution
    io.write("\n  Query Distribution:\n")
    for i, q in ipairs(queries) do
        io.write(string.format("    - %s: %.0f%%\n", q.name, q.weight * 100))
    end
    io.write("\n")
end
