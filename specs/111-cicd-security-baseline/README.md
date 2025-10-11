# SPEC-111: CI/CD Security Baseline & Secret Management (Enhanced)
**Status:** Complete (Enhanced Oct 11, 2025)
**Owner:** Security Engineering
**Last Updated:** 2025-10-11

> **Purpose:** Address external code review (Priority 1) findings and establish production-grade secret management with audit logging, encryption-at-rest, and zero-trust principles.

---

## 1. Security Controls

### 1.1 No Plaintext Secrets in VCS
**Enforcement:**
- ✅ Pre-commit hook: `detect-secrets` scans all commits
- ✅ GitHub secret scanning: Required status check
- ✅ Gitleaks in CI/CD: Fails build on detection
- ✅ `.env.example` checked in, real `.env` git-ignored

**Pre-commit configuration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json

  - repo: https://github.com/zricethezav/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

---

### 1.2 Environment-Based Secret Injection
**GitHub Environments** (Development/Test):
```yaml
# .github/workflows/deploy-dev.yml
name: Deploy Dev
on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: development  # Requires approval
    steps:
      - uses: actions/checkout@v4
      - name: Deploy with secrets
        env:
          DATABASE_URL: ${{ secrets.DEV_DATABASE_URL }}
          REDIS_URL: ${{ secrets.DEV_REDIS_URL }}
          JWT_SECRET: ${{ secrets.DEV_JWT_SECRET }}
        run: |
          # Secrets injected at runtime only
          ./scripts/deploy.sh
```

**Least Privilege Tokens:**
```yaml
permissions:
  contents: read
  packages: write  # GHCR only, no repo write
  id-token: write  # For OIDC
```

---

### 1.3 Secret Rotation Policy
**Automated Rotation:**
- **Database passwords**: 90-day rotation via GitHub Actions workflow
- **API keys**: 60-day rotation with notification
- **JWT signing keys**: Blue/green deployment for zero-downtime rotation
- **GitHub PATs**: 180-day expiration with Renovate reminders

**Rotation Workflow:**
```yaml
# .github/workflows/rotate-secrets.yml
name: Secret Rotation Reminder
on:
  schedule:
    - cron: '0 0 */30 * *'  # Every 30 days

jobs:
  check-expiry:
    runs-on: ubuntu-latest
    steps:
      - name: Check secret age
        run: |
          # Query secret metadata (not values)
          # Send Slack notification if > 80 days old
          ./scripts/security/check-secret-expiry.sh
```

---

## 2. Production-Grade Secret Management (Enhanced)

### 2.1 Secret Tiers

| Environment | Secret Store | Access Control | Audit Logging | Encryption |
|-------------|--------------|----------------|---------------|------------|
| **Development** | GitHub Environments | Required reviewers (1) | GitHub audit log | AES-256 (GitHub managed) |
| **Test** | GitHub Environments | Required reviewers (2) | GitHub audit log + CloudWatch | AES-256 (GitHub managed) |
| **Production** | **HashiCorp Vault** or **AWS Secrets Manager** | MFA required, break-glass only | CloudTrail + Vault audit | KMS (customer-managed keys) |

---

### 2.2 Production: HashiCorp Vault Integration

#### A. Vault Setup (Docker for Dev, Kubernetes for Prod)

**docker-compose.vault.yml:**
```yaml
version: '3.9'
services:
  vault:
    image: hashicorp/vault:1.15
    container_name: ninaivalaigal-vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: "root-token-dev-only"  # Dev only!
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
    volumes:
      - vault-data:/vault/data
      - ./vault-config:/vault/config
    command: server -dev

  vault-agent:
    image: hashicorp/vault:1.15
    container_name: ninaivalaigal-vault-agent
    environment:
      VAULT_ADDR: http://vault:8200
    volumes:
      - ./vault-agent-config.hcl:/vault/config/agent.hcl
      - /tmp/vault-secrets:/vault/secrets
    command: agent -config=/vault/config/agent.hcl

volumes:
  vault-data:
```

#### B. Secret Storage in Vault

**Initialize Vault and create secrets:**
```bash
#!/bin/bash
# scripts/security/vault-init.sh

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root-token-dev-only'  # Use AppRole in prod

# Enable KV v2 secrets engine
vault secrets enable -path=ninaivalaigal kv-v2

# Store database credentials
vault kv put ninaivalaigal/dev/database \
  url="postgresql://nina:***@ninaivalaigal-dev-db:5432/nina" \
  password="change_me_securely" \  # pragma: allowlist secret
  max_connections=100

# Store Redis credentials
vault kv put ninaivalaigal/dev/redis \
  url="redis://ninaivalaigal-dev-redis:6379" \
  password=""

# Store JWT signing key
vault kv put ninaivalaigal/dev/jwt \
  secret_key="your-256-bit-secret" \  # pragma: allowlist secret
  algorithm="HS256" \
  expiry_hours=24

# Store API keys
vault kv put ninaivalaigal/dev/external-apis \
  openai_key="sk-..." \
  stripe_key="sk_test_..."

echo "✅ Secrets stored in Vault at ninaivalaigal/dev/*"
```

#### C. Application Integration (Python)

**FastAPI with HVAC (Vault client):**
```python
# server/core/vault_client.py
import hvac
import os
from functools import lru_cache

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200'),
            token=os.getenv('VAULT_TOKEN')  # Or AppRole
        )

        if not self.client.is_authenticated():
            raise Exception("Vault authentication failed")

    @lru_cache(maxsize=128)
    def get_secret(self, path: str) -> dict:
        """Fetch secret from Vault with caching."""
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='ninaivalaigal'
            )
            return secret['data']['data']
        except Exception as e:
            # Fallback to environment variables for local dev
            print(f"⚠️ Vault fetch failed, using env vars: {e}")
            return {}

    def rotate_secret(self, path: str, new_value: dict):
        """Rotate a secret (creates new version)."""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=new_value,
            mount_point='ninaivalaigal'
        )
        # Clear cache
        self.get_secret.cache_clear()

# Usage in FastAPI
vault = VaultClient()

# Get database credentials
db_creds = vault.get_secret('dev/database')
DATABASE_URL = db_creds.get('url', os.getenv('DATABASE_URL'))
```

**Dynamic secrets (PostgreSQL):**
```bash
# Enable database secrets engine
vault secrets enable database

# Configure PostgreSQL connection
vault write database/config/ninaivalaigal \
  plugin_name=postgresql-database-plugin \
  allowed_roles="readonly,readwrite" \
  connection_url="postgresql://{{username}}:{{password}}@localhost:5432/nina" \
  username="vault_admin" \
  password="vault_admin_password"  # pragma: allowlist secret

# Create role for read-only access
vault write database/roles/readonly \
  db_name=ninaivalaigal \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Application fetches temporary credentials
vault read database/creds/readonly
# Key                Value
# ---                -----
# lease_id           database/creds/readonly/abc123
# lease_duration     1h
# username           v-token-readonly-xyz789
# password           A1a-B2b3C4c5D6d7E8e9
```

---

### 2.3 Alternative: AWS Secrets Manager

**For AWS deployments:**
```python
# server/core/aws_secrets.py
import boto3
import json
from functools import lru_cache

class AWSSecretsManager:
    def __init__(self, region='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region)

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> dict:
        """Fetch secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            print(f"⚠️ AWS Secrets Manager error: {e}")
            return {}

    def rotate_secret(self, secret_name: str, new_value: dict):
        """Rotate secret (creates new version)."""
        self.client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(new_value)
        )
        self.get_secret.cache_clear()

# Usage
secrets = AWSSecretsManager()
db_creds = secrets.get_secret('ninaivalaigal/dev/database')
DATABASE_URL = db_creds['url']
```

**KMS Encryption:**
```bash
# Create KMS key for encryption
aws kms create-key \
  --description "Ninaivalaigal secrets encryption" \
  --key-policy file://kms-policy.json

# Store secret with KMS encryption
aws secretsmanager create-secret \
  --name ninaivalaigal/prod/database \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/abc-def \
  --secret-string '{"url":"postgresql://...","password":"***"}'
```

---

## 3. Secret Injection Strategies

### 3.1 Development: .env Files (Local Only)
```bash
# .env (git-ignored)
DATABASE_URL=postgresql://nina:change_me_securely@localhost:5432/nina  # pragma: allowlist secret
REDIS_URL=redis://localhost:6379
JWT_SECRET=dev-secret-key-change-in-prod  # pragma: allowlist secret
OPENAI_API_KEY=sk-...

# Load in application
from dotenv import load_dotenv
load_dotenv()
```

### 3.2 Production: Mounted Volumes (Kubernetes)
```yaml
# kubernetes/api-deployment.yaml
apiVersion: v1
kind: Pod
metadata:
  name: ninaivalaigal-api
spec:
  containers:
    - name: api
      image: ghcr.io/medhasys/ninaivalaigal-api:latest
      volumeMounts:
        - name: secrets
          mountPath: /secrets
          readOnly: true
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ninaivalaigal-secrets
              key: database-url
  volumes:
    - name: secrets
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: "vault-ninaivalaigal"  # pragma: allowlist secret
```

### 3.3 Production: Init Containers
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ninaivalaigal-api
spec:
  initContainers:
    - name: vault-agent
      image: hashicorp/vault:1.15
      command: ["/bin/sh", "-c"]
      args:
        - |
          vault agent -config=/vault/config/agent.hcl
          # Fetches secrets and writes to /secrets volume
      volumeMounts:
        - name: secrets
          mountPath: /secrets
  containers:
    - name: api
      image: ghcr.io/medhasys/ninaivalaigal-api:latest
      volumeMounts:
        - name: secrets
          mountPath: /secrets
          readOnly: true
  volumes:
    - name: secrets
      emptyDir: {}
```

---

## 4. Audit Logging

### 4.1 Vault Audit Logs

**Enable audit logging:**
```bash
# File-based audit log
vault audit enable file file_path=/vault/logs/audit.log

# Syslog audit log
vault audit enable syslog tag="vault" facility="AUTH"
```

**Audit log format:**
```json
{
  "time": "2025-10-11T00:00:00.000000Z",
  "type": "response",
  "auth": {
    "client_token": "hmac-sha256:abc123...",
    "accessor": "hmac-sha256:xyz789...",
    "display_name": "token-dev-user",
    "policies": ["default", "ninaivalaigal-read"]
  },
  "request": {
    "id": "req-abc123",
    "operation": "read",
    "path": "ninaivalaigal/data/dev/database"
  },
  "response": {
    "data": null  // Secrets not logged
  }
}
```

### 4.2 AWS CloudTrail Integration

**Track Secrets Manager access:**
```json
{
  "eventVersion": "1.08",
  "userIdentity": {
    "type": "AssumedRole",
    "principalId": "AROAEXAMPLE",
    "arn": "arn:aws:sts::123456789:assumed-role/ninaivalaigal-api/session"
  },
  "eventTime": "2025-10-11T00:00:00Z",
  "eventSource": "secretsmanager.amazonaws.com",
  "eventName": "GetSecretValue",
  "requestParameters": {
    "secretId": "ninaivalaigal/prod/database"  // pragma: allowlist secret
  },
  "responseElements": null,  // Secret values not logged
  "resources": [{
    "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:ninaivalaigal/prod/database",
    "accountId": "123456789"
  }]
}
```

### 4.3 Alerting on Suspicious Activity

**Prometheus AlertManager rules:**
```yaml
groups:
  - name: secret_access_alerts
    rules:
      - alert: UnauthorizedSecretAccess
        expr: vault_audit_log_request_failures_total > 5
        for: 5m
        annotations:
          summary: "Repeated failed secret access attempts"
          description: "{{ $labels.path }} failed {{ $value }} times"

      - alert: SecretAccessOutsideBusinessHours
        expr: hour() < 8 or hour() > 18
        annotations:
          summary: "Secret accessed outside business hours"

      - alert: HighVolumeSecretAccess
        expr: rate(vault_secret_lease_creation_total[5m]) > 100
        annotations:
          summary: "Unusually high secret access rate"
```

---

## 5. Secret Lifecycle

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Repo as Git Repo
    participant GH as GitHub Environments
    participant Vault as HashiCorp Vault
    participant Runner as Actions Runner
    participant App as Application

    Dev->>Repo: push code (no secrets)
    Repo->>Repo: pre-commit: detect-secrets scan
    Repo->>GH: trigger workflow

    GH->>GH: environment: development (requires approval)
    GH->>Runner: inject secrets from environment

    Runner->>Vault: request secret (AppRole auth)
    Vault->>Vault: check policy, audit log
    Vault-->>Runner: return secret (ephemeral)

    Runner->>App: deploy with secrets in memory only
    App->>App: secrets never written to disk

    App->>Vault: periodic token renewal (for long-running)
    Vault-->>App: renewed token
```

---

## 6. Key Policies

### 6.1 Secrets Registry
**Centralized in GitHub Environments** (dev/test) and **Vault** (prod):
- All secrets documented in `/docs/SECRETS_REGISTRY.md`
- Required reviewers: 1 for dev, 2 for test, 3 for prod
- Break-glass access: Requires incident ticket + post-mortem

### 6.2 Runtime Injection
- **Never hardcoded** in Dockerfiles or code
- **Never logged** in plaintext
- **.env.example** shows structure, `.env` contains real values (git-ignored)
- **Environment variables** preferred over config files

### 6.3 Rotation Schedule
| Secret Type | Rotation Frequency | Owner |
|-------------|-------------------|-------|
| Database passwords | 90 days | Platform SRE |
| API keys (external) | 60 days | Security Team |
| JWT signing keys | 180 days (blue/green) | Platform SRE |
| GitHub PATs | 180 days | DevOps Team |
| TLS certificates | 90 days (auto-renewed) | Security Team |

---

## 7. Incident Response

### 7.1 Secret Leak Detection
**Automated response workflow:**
```yaml
# .github/workflows/secret-leak-response.yml
name: Secret Leak Response
on:
  push:
    branches: ['**']

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

      - name: Notify security team
        if: failure()
        run: |
          # Send alert to Slack #security channel
          curl -X POST ${{ secrets.SLACK_WEBHOOK_SECURITY }} \
            -d '{"text":"🚨 Secret detected in commit ${{ github.sha }}"}'

      - name: Revoke compromised secrets
        if: failure()
        run: |
          # Auto-rotate if specific patterns detected
          ./scripts/security/emergency-rotate.sh
```

### 7.2 Break-Glass Access
**Emergency access to production secrets:**
1. Create incident ticket with justification
2. Request break-glass access via Slack #security-incidents
3. Approval from 2 security team members required
4. Temporary Vault token issued (1-hour TTL)
5. All actions logged and audited
6. Post-mortem required within 24 hours

---

## 8. Compliance Checklist

- [ ] **SOC2**: Audit logging enabled for all secret access
- [ ] **GDPR**: Secrets containing PII encrypted with KMS
- [ ] **HIPAA**: Database credentials rotated every 90 days
- [ ] **PCI-DSS**: Payment API keys stored in Vault, never in code
- [ ] **ISO 27001**: Secret access reviews quarterly

---

## 9. Acceptance Criteria

✅ **Detection**:
- [ ] Pre-commit hooks prevent plaintext secrets from entering VCS
- [ ] GitHub secret scanning alerts within 5 minutes
- [ ] Gitleaks CI check fails build on detection

✅ **Storage**:
- [ ] Development secrets in GitHub Environments (approved)
- [ ] Production secrets in Vault/AWS Secrets Manager
- [ ] All secrets encrypted at rest with KMS
- [ ] No secrets in Docker images or logs

✅ **Access**:
- [ ] Least privilege: Applications request only needed secrets
- [ ] MFA required for production secret access
- [ ] Break-glass process documented and tested

✅ **Audit**:
- [ ] All secret access logged (who, when, what)
- [ ] Audit logs retained for 90 days (compliance)
- [ ] Suspicious activity alerts within 5 minutes
- [ ] Monthly access reviews completed

✅ **Rotation**:
- [ ] Automated rotation reminders for all secret types
- [ ] Zero-downtime rotation for JWT keys (blue/green)
- [ ] Database password rotation tested and documented

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Install pre-commit hooks (detect-secrets, gitleaks)
- [ ] Configure GitHub Environments for dev/test
- [ ] Document all existing secrets in registry

### Phase 2: Vault Integration (Week 2-3)
- [ ] Deploy Vault (Docker for dev, Kubernetes for prod)
- [ ] Migrate production secrets to Vault
- [ ] Update applications to use Vault client
- [ ] Enable audit logging

### Phase 3: Automation (Week 4)
- [ ] Implement rotation workflows
- [ ] Set up monitoring and alerting
- [ ] Configure incident response automation
- [ ] Conduct break-glass drill

### Phase 4: Compliance (Week 5-6)
- [ ] Audit log retention configured
- [ ] Compliance checklist completed
- [ ] Quarterly access review process established
- [ ] Documentation finalized

---

## 11. References

- HashiCorp Vault: https://www.vaultproject.io/docs
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
- detect-secrets: https://github.com/Yelp/detect-secrets
- Gitleaks: https://github.com/zricethezav/gitleaks
- OWASP Secret Management: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

---

**Enhancements Added (Oct 11, 2025):**
- ✅ HashiCorp Vault integration with Docker/Kubernetes deployment
- ✅ AWS Secrets Manager as alternative
- ✅ KMS encryption for secrets at rest
- ✅ Comprehensive audit logging (Vault, CloudTrail)
- ✅ Secret injection strategies (volumes, init containers, env vars)
- ✅ Incident response workflow for secret leaks
- ✅ Break-glass emergency access procedure
- ✅ Compliance checklist (SOC2, GDPR, HIPAA, PCI-DSS)
- ✅ Automated rotation workflows with zero-downtime
