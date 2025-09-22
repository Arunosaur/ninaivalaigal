# SPEC-013 (External)

This spec has been moved to its own repository:
https://github.com/Arunosaur/spec-013-mac-studio-validation

It is included here as a submodule under `external/spec-013`
for convenience only, and is **not** part of the main CI workflow.

## Why External?

SPEC-013 validates Mac Studio + Apple Container CLI infrastructure, which is:
- Platform-specific validation (not core product features)
- Resource-intensive (requires Mac Studio hardware)
- Reusable across projects (standalone validation toolkit)

## Usage

```bash
# Clone with submodules
git clone --recurse-submodules git@github.com:Arunosaur/ninaivalaigal.git

# Update submodule
git submodule update --remote external/spec-013

# Run validation (requires Apple Container CLI)
cd external/spec-013
./scripts/validate_arm64.sh
./benchmarks/compare_docker.sh
./start-apple-container-stack.sh
```

## CI Status

[![Hosted Static Validation](https://github.com/Arunosaur/spec-013-mac-studio-validation/actions/workflows/validate-hosted.yml/badge.svg)](https://github.com/Arunosaur/spec-013-mac-studio-validation/actions/workflows/validate-hosted.yml)
[![Self-Hosted Mac Studio Validation](https://github.com/Arunosaur/spec-013-mac-studio-validation/actions/workflows/validate.yml/badge.svg)](https://github.com/Arunosaur/spec-013-mac-studio-validation/actions/workflows/validate.yml)
