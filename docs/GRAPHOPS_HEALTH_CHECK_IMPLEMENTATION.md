# GraphOps Health Check Implementation Guide

**For:** Developer A
**Task:** #49 - GraphOps Containerization
**Priority:** HIGH

---

## 🎯 Objective

Add a `--health-check` CLI flag to GraphOps that:
1. Performs a quick health probe
2. Exits immediately with exit code 0 (success) or 1 (failure)
3. Takes <1 second to run
4. Works without full environment configuration

---

## 📛 Naming Convention

**Image Name:** `ninaivalaigal-graphops:arm64`
**Container Name:** `ninaivalaigal-dev-graphops`

**Pattern:**
- Images: `ninaivalaigal-{service}:{tag}`
- Containers: `ninaivalaigal-{env}-{service}`

Do NOT use `nina-graphops` or add runtime suffixes like `-apple`.

---

## 📝 Implementation Steps

### **1. Update CLI Arguments (clap)**

Location: `rust-services/graphops/src/main.rs` or `src/cli.rs`

```rust
use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "graphops")]
#[command(about = "GraphOps gRPC Server", long_about = None)]
struct Cli {
    /// Run health check and exit
    #[arg(long, help = "Perform health check and exit")]
    health_check: bool,

    /// Database connection string
    #[arg(env = "DATABASE_URL")]
    database_url: Option<String>,

    /// Graph name
    #[arg(env = "GRAPHOPS_GRAPH")]
    graph: Option<String>,

    // ... other existing flags
}
```

### **2. Add Health Check Function**

```rust
use std::process;

/// Quick health check - validates binary can start
fn run_health_check(cli: &Cli) -> anyhow::Result<()> {
    println!("🏥 Running GraphOps health check...");

    // 1. Basic checks (always run)
    println!("  ✅ Binary executable");

    // 2. Configuration check (if env vars provided)
    if let Some(db_url) = &cli.database_url {
        println!("  ✅ DATABASE_URL configured");

        // Optional: Quick DB connection test (with timeout)
        // Only if you want to validate DB connectivity
        // match test_db_connection(db_url) {
        //     Ok(_) => println!("  ✅ Database connection OK"),
        //     Err(e) => {
        //         eprintln!("  ⚠️  Database connection failed: {}", e);
        //         // Don't fail health check - just warn
        //     }
        // }
    }

    if cli.graph.is_some() {
        println!("  ✅ GRAPHOPS_GRAPH configured");
    }

    println!("✅ GraphOps health check PASSED");
    Ok(())
}

/// Optional: Quick database connection test with timeout
#[cfg(feature = "db-health-check")]
fn test_db_connection(db_url: &str) -> anyhow::Result<()> {
    use tokio::time::{timeout, Duration};

    let runtime = tokio::runtime::Runtime::new()?;
    runtime.block_on(async {
        timeout(Duration::from_secs(2), async {
            // Your DB connection code here
            // sqlx::PgPool::connect(db_url).await?;
            Ok::<(), anyhow::Error>(())
        }).await??;
        Ok(())
    })
}
```

### **3. Update Main Function**

```rust
fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // Handle health check mode FIRST (before any heavy initialization)
    if cli.health_check {
        match run_health_check(&cli) {
            Ok(_) => process::exit(0),  // Success
            Err(e) => {
                eprintln!("❌ Health check failed: {}", e);
                process::exit(1);  // Failure
            }
        }
    }

    // Normal server startup continues here
    println!("🚀 Starting GraphOps server...");

    // ... existing server initialization code
    start_server(cli)?;

    Ok(())
}
```

---

## 🧪 Testing

### **1. Build Updated Binary**

```bash
# In rust-services/graphops/
cargo build --release

# Or rebuild container
docker build --no-cache --platform linux/arm64 \
  -t ninaivalaigal-graphops:arm64 \
  -f containers/graphops-rust/Dockerfile .
```

### **2. Test Health Check Locally**

```bash
# Test without env vars (should still pass)
./target/release/graphops --health-check

# Expected output:
# 🏥 Running GraphOps health check...
#   ✅ Binary executable
# ✅ GraphOps health check PASSED

# Test with env vars
DATABASE_URL=postgresql://localhost/test \
GRAPHOPS_GRAPH=test_graph \
./target/release/graphops --health-check

# Expected output:
# 🏥 Running GraphOps health check...
#   ✅ Binary executable
#   ✅ DATABASE_URL configured
#   ✅ GRAPHOPS_GRAPH configured
# ✅ GraphOps health check PASSED
```

### **3. Test in Container**

```bash
# Quick health check (should exit immediately)
docker run --rm ninaivalaigal-graphops:arm64 --health-check

# Should see:
# ✅ GraphOps health check PASSED
# (and container exits with code 0)

# Check exit code
docker run --rm ninaivalaigal-graphops:arm64 --health-check
echo $?  # Should print: 0
```

### **4. Test Docker HEALTHCHECK**

Update Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/usr/local/bin/graphops", "--health-check"]
```

Then:
```bash
docker build -t ninaivalaigal-graphops:arm64-healthcheck .

# Start container
docker run -d --name graphops-test \
  -e DATABASE_URL=postgresql://... \
  ninaivalaigal-graphops:arm64-healthcheck

# Check health status (wait ~5 seconds for start period)
docker ps  # Should show "healthy" in STATUS column

# View health check logs
docker inspect graphops-test | jq '.[0].State.Health'

# Cleanup
docker stop graphops-test && docker rm graphops-test
```

---

## 📋 Verification Checklist

- [ ] `--health-check` flag added to CLI
- [ ] Health check function implemented
- [ ] Function exits with code 0 on success
- [ ] Function exits with code 1 on failure
- [ ] Execution time <1 second
- [ ] Works without DATABASE_URL
- [ ] Works with DATABASE_URL
- [ ] Local cargo build succeeds
- [ ] Container build succeeds
- [ ] Container health check exits immediately
- [ ] Docker HEALTHCHECK working
- [ ] Documentation updated

---

## 🎯 Minimal Implementation

If you want the **absolute minimum** implementation:

```rust
// In main.rs
use clap::Parser;

#[derive(Parser)]
struct Cli {
    #[arg(long)]
    health_check: bool,
}

fn main() {
    let cli = Cli::parse();

    if cli.health_check {
        println!("✅ GraphOps healthy");
        std::process::exit(0);
    }

    // Normal server code...
}
```

That's it! Even this minimal version is enough for Docker health checks.

---

## 🚀 Expected Timeline

- **Implementation:** 15-30 minutes
- **Testing:** 15-30 minutes
- **Container rebuild:** 5-10 minutes
- **Documentation:** 10 minutes
- **Total:** ~1 hour

---

## 📊 Success Criteria

**Before:**
```bash
docker run --rm ninaivalaigal-graphops:arm64 --health-check
# ❌ Hangs indefinitely waiting for server shutdown
```

**After:**
```bash
docker run --rm ninaivalaigal-graphops:arm64 --health-check
# ✅ GraphOps healthy
# (exits immediately with code 0)
```

---

## 🔗 Next Steps After Implementation

1. ✅ Rebuild container with health check
2. ✅ Test health check in isolation
3. ✅ Update Task #49 status to "Done"
4. ✅ Document env vars in Task #77
5. ✅ Integrate with API Gateway (Task #83)
6. ✅ Update deployment documentation

---

**Reference:** This follows the same pattern used in Go services for health checks.

**Questions?** Let Developer C know if you need help with the Rust implementation.
