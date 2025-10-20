# Task #77: CLI Tools Distribution Checklist

**Developer:** Developer A
**Status:** Ready for Distribution
**Date:** October 20, 2025

---

## ✅ **Pre-Distribution Checklist**

### **Build Artifacts Ready:**
- [x] CLI rebuilt with correct ports (v1.0.0-compliance-92-gad69d72d)
- [x] 4 platform packages in `go-services/cli-tools/dist/`
- [x] SHA-256 checksums.txt generated
- [x] TASK_77_CLI_TOOLS_DEPLOYMENT.md updated
- [x] GraphOps gRPC-only behavior documented

### **Validation Complete:**
- [x] ./nina --version works
- [x] ./nina health check --json tested
- [x] core-api: healthy (13390)
- [x] gateway: healthy (13395)
- [x] memory: healthy (13393)
- [x] graphops: EOF expected (gRPC-only, port 13398)

---

## 📦 **Distribution Steps**

### **Step 1: Verify Artifacts**
```bash
cd /Users/swami/WorkSpace/ninaivalaigal/go-services/cli-tools/dist

# Check all files present
ls -lh
# Should show:
# nina-v1.0.0-compliance-92-gad69d72d-darwin-amd64.tar.gz (8.2 MB)
# nina-v1.0.0-compliance-92-gad69d72d-darwin-arm64.tar.gz (7.7 MB)
# nina-v1.0.0-compliance-92-gad69d72d-linux-amd64.tar.gz (8.0 MB)
# nina-v1.0.0-compliance-92-gad69d72d-windows-amd64.zip (8.2 MB)
# checksums.txt

# Verify checksums
shasum -a 256 -c checksums.txt
# Should show: ✓ OK for all files
```

### **Step 2: Upload to Distribution Target**

**Option A: Apple Container Host (SCP)**
```bash
# Upload to Apple host
scp go-services/cli-tools/dist/* apple-host:/opt/ninaivalaigal/cli-tools/

# Or specific platform only
scp go-services/cli-tools/dist/nina-*-darwin-arm64.tar.gz apple-host:/tmp/
scp go-services/cli-tools/dist/checksums.txt apple-host:/tmp/
```

**Option B: Internal Artifact Store**
```bash
# Example: AWS S3
aws s3 cp go-services/cli-tools/dist/ s3://ninaivalaigal-artifacts/cli-tools/v1.0.0/ --recursive

# Example: GitHub Releases
gh release create v1.0.0-cli \
  go-services/cli-tools/dist/nina-*.tar.gz \
  go-services/cli-tools/dist/nina-*.zip \
  go-services/cli-tools/dist/checksums.txt \
  --title "Nina CLI Tools v1.0.0" \
  --notes "See docs/TASK_77_CLI_TOOLS_DEPLOYMENT.md for details"
```

**Option C: Shared Network Drive**
```bash
# Copy to shared location
cp go-services/cli-tools/dist/* /Volumes/SharedDrive/ninaivalaigal/cli-tools/
```

### **Step 3: Notify Team**

Create notification message:

```markdown
📢 **Nina CLI Tools v1.0.0 Available**

The unified CLI is ready for deployment!

**Distribution Location:**
- [Location where you uploaded files]

**Documentation:**
https://github.com/yourorg/ninaivalaigal/blob/main/docs/TASK_77_CLI_TOOLS_DEPLOYMENT.md

**Quick Install (macOS ARM64):**
```bash
# Download and extract
tar -xzf nina-v1.0.0-compliance-92-gad69d72d-darwin-arm64.tar.gz -C /usr/local/bin/

# Verify
nina --version
# Should show: nina version 1.0.0

# Test
nina health check --json
```

**Important Note about GraphOps:**
GraphOps is a gRPC-only service and will show "unhealthy" with EOF in the CLI health check. This is expected behavior. To check GraphOps health:
```bash
container exec ninaivalaigal-dev-graphops /usr/local/bin/graphops --health-check
# Or: grpcurl -plaintext localhost:13398 list
```

**Checksums for Verification:**
See `checksums.txt` for SHA-256 values.

**Questions?** Contact Developer A or see deployment runbook.
```

### **Step 4: Send to Ops/Developer B**

**Email/Slack Template:**
```
Subject: Nina CLI Tools v1.0.0 - Ready for Deployment

Hi Ops Team / Developer B,

The unified Nina CLI tools are now ready for deployment. All port configurations have been corrected and tested.

📋 Deployment Guide:
docs/TASK_77_CLI_TOOLS_DEPLOYMENT.md

📦 Artifacts Location:
[Your distribution location]

✅ What's Working:
- Core API health check (port 13390)
- Gateway health check (port 13395)
- Memory Service health check (port 13393)

⚠️ GraphOps Note:
GraphOps is a gRPC-only service. The CLI health check will show "unhealthy" with EOF - this is EXPECTED. Use these commands to verify GraphOps:
```bash
container exec ninaivalaigal-dev-graphops /usr/local/bin/graphops --health-check
grpcurl -plaintext localhost:13398 list
```

🔧 Installation:
See deployment guide for platform-specific instructions.

Let me know if you need any help with deployment!

- Developer A
```

---

## 📋 **Post-Distribution Checklist**

- [ ] Artifacts uploaded to distribution target
- [ ] Checksums.txt available for verification
- [ ] Ops team notified with documentation link
- [ ] Developer B notified with GraphOps note
- [ ] Installation tested on target environment
- [ ] Taiga Task #77 marked as "Deployed"

---

## 🔍 **Validation on Target Environment**

Once installed on the target system:

```bash
# 1. Verify installation
nina --version

# 2. Check configuration
nina config show --format json

# 3. Test health checks
nina health check --json

# 4. Verify GraphOps separately (if needed)
container exec ninaivalaigal-dev-graphops /usr/local/bin/graphops --health-check
```

---

## 📞 **Support Contact**

**Technical Issues:** Developer A
**Deployment Questions:** Operations Team
**API Endpoint Issues:** Developer B

**Documentation:**
- Main: `docs/TASK_77_CLI_TOOLS_DEPLOYMENT.md`
- Setup Guide: `go-services/cli-tools/README.md`
- Port Allocation: `config/ports.nv.yaml`

---

**Task #77 is ready for production deployment!** ✅
