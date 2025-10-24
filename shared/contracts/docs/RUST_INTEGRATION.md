# Rust Service Integration

**Purpose:** Protobuf + Tonic integration for Rust services
**Status:** Future-Ready (SPEC-099 Phase 2)

---

## Quick Start (Future)

```rust
// Cargo.toml
[dependencies]
tonic = "0.10"
prost = "0.12"

[build-dependencies]
tonic-build = "0.10"
```

```rust
// build.rs
fn main() {
    tonic_build::compile_protos("../../shared/contracts/graphops/v1/graphops.proto")
        .unwrap();
}
```

```rust
// src/main.rs
pub mod graphops {
    tonic::include_proto!("ninaivalaigal.graphops.v1");
}

use graphops::{CypherRequest, CypherResponse};
```

---

## Type Mappings

| Python | Protobuf | Rust |
|--------|----------|------|
| str | string | String |
| int | int32/int64 | i32/i64 |
| float | float/double | f32/f64 |
| bool | bool | bool |
| list | repeated | Vec<T> |

---

## References
- [Tonic](https://docs.rs/tonic/)
- [SPEC-099](../../../specs/099-rust-migration-strategy/README.md)
