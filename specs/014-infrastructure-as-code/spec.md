# SPEC-014: Infrastructure as Code (Terraform)

## Overview

This specification defines the Infrastructure as Code (IaC) strategy for ninaivalaigal using Terraform, enabling repeatable, version-controlled, multi-cloud infrastructure deployment with proper state management and automation.

## Motivation

- **Repeatable Deployments**: Infrastructure defined as code for consistent environments
- **Multi-Cloud Strategy**: Support AWS, GCP, and Azure with unified tooling
- **Version Control**: Infrastructure changes tracked and reviewed like application code
- **Automation**: Integrated with CI/CD for automated infrastructure updates
- **Cost Management**: Predictable resource provisioning and cleanup

## Specification

### 1. Multi-Cloud Architecture

#### 1.1 Supported Cloud Providers
```
AWS:    ECS Fargate + Application Load Balancer + CloudWatch
GCP:    Cloud Run + Cloud SQL + Cloud Monitoring
Azure:  Container Instances + PostgreSQL + Azure Monitor
```

#### 1.2 Service Mapping
| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Compute** | ECS Fargate | Cloud Run | Container Instances |
| **Database** | RDS PostgreSQL | Cloud SQL | Azure Database |
| **Load Balancer** | ALB | Cloud Load Balancing | Azure Load Balancer |
| **Monitoring** | CloudWatch | Cloud Monitoring | Azure Monitor |
| **Networking** | VPC + Security Groups | VPC + Firewall | VNet + NSG |

### 2. Terraform Module Structure

#### 2.1 Directory Organization
```
terraform/
├── aws/
│   ├── main.tf           # AWS ECS infrastructure
│   ├── variables.tf      # Input variables
│   ├── outputs.tf        # Output values
│   └── terraform.tfvars.example
├── gcp/
│   ├── main.tf           # GCP Cloud Run infrastructure
│   ├── variables.tf      # Input variables
│   ├── outputs.tf        # Output values
│   └── terraform.tfvars.example
└── azure/
    ├── main.tf           # Azure Container Instances
    ├── variables.tf      # Input variables
    ├── outputs.tf        # Output values
    └── terraform.tfvars.example
```

#### 2.2 Common Variables
```hcl
# Required for all providers
variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret for authentication"
  type        = string
  sensitive   = true
}
```

### 3. AWS Infrastructure (ECS Fargate)

#### 3.1 Core Components
```hcl
Resources:
  - aws_ecs_cluster.ninaivalaigal
  - aws_ecs_task_definition.ninaivalaigal_api
  - aws_ecs_service.ninaivalaigal_api
  - aws_lb.ninaivalaigal (Application Load Balancer)
  - aws_lb_target_group.ninaivalaigal
  - aws_security_group.alb
  - aws_security_group.ecs_tasks
  - aws_iam_role.ecs_execution_role
  - aws_cloudwatch_log_group.ninaivalaigal
```

#### 3.2 Container Configuration
```hcl
Container Image: ghcr.io/arunosaur/ninaivalaigal-api:latest
CPU: 256 (0.25 vCPU)
Memory: 512 MB
Port: 8000
Health Check: /health endpoint
Logging: CloudWatch Logs
```

### 4. GCP Infrastructure (Cloud Run)

#### 4.1 Core Components
```hcl
Resources:
  - google_cloud_run_service.ninaivalaigal_api
  - google_cloud_run_service_iam_member.public_access
  - google_project_service.cloud_run_api
  - google_sql_database_instance.postgres (optional)
  - google_sql_database.ninaivalaigal_db (optional)
  - google_sql_user.ninaivalaigal_user (optional)
```

#### 4.2 Serverless Configuration
```hcl
Container Image: ghcr.io/arunosaur/ninaivalaigal-api:latest
CPU: 1000m (1 vCPU)
Memory: 512Mi
Concurrency: 100
Auto-scaling: 1-10 instances
Health Check: /health endpoint
```

### 5. Azure Infrastructure (Container Instances)

#### 5.1 Core Components
```hcl
Resources:
  - azurerm_resource_group.ninaivalaigal
  - azurerm_container_group.ninaivalaigal_api
  - azurerm_postgresql_flexible_server.postgres (optional)
  - azurerm_postgresql_flexible_server_database.ninaivalaigal_db (optional)
  - azurerm_postgresql_flexible_server_firewall_rule.allow_all (optional)
```

#### 5.2 Container Configuration
```hcl
Container Image: ghcr.io/arunosaur/ninaivalaigal-api:latest
CPU: 1 core
Memory: 1.5 GB
Public IP: Yes
DNS Label: ninaivalaigal-api-{random}
Health Check: /health endpoint
```

## Implementation

### 1. Makefile Integration
```makefile
# AWS Infrastructure
terraform-init-aws:     # Initialize Terraform for AWS
terraform-plan-aws:     # Plan AWS deployment
terraform-apply-aws:    # Apply AWS infrastructure
terraform-destroy-aws:  # Destroy AWS infrastructure

# GCP Infrastructure
terraform-init-gcp:     # Initialize Terraform for GCP
terraform-plan-gcp:     # Plan GCP deployment
terraform-apply-gcp:    # Apply GCP infrastructure
terraform-destroy-gcp:  # Destroy GCP infrastructure

# Azure Infrastructure
terraform-init-azure:   # Initialize Terraform for Azure
terraform-plan-azure:   # Plan Azure deployment
terraform-apply-azure:  # Apply Azure infrastructure
terraform-destroy-azure: # Destroy Azure infrastructure
```

### 2. GitHub Actions Integration
```yaml
# .github/workflows/infra-deploy.yml
Workflow: Infrastructure Deployment
Triggers:
  - workflow_dispatch (manual)
  - Infrastructure changes (future)

Inputs:
  - cloud_provider: aws|gcp|azure
  - action: plan|apply|destroy

Authentication:
  - AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  - GCP: GCP_SA_KEY (service account JSON)
  - Azure: AZURE_CREDENTIALS
```

### 3. State Management
```hcl
# Terraform Backend (recommended for production)
terraform {
  backend "s3" {    # AWS S3 backend
    bucket = "ninaivalaigal-terraform-state"
    key    = "aws/terraform.tfstate"
    region = "us-west-2"
  }
}

# Alternative: Local state for development
# terraform {
#   backend "local" {}
# }
```

## Security Considerations

### 1. Secrets Management
```hcl
# Sensitive variables
variable "database_url" {
  sensitive = true
}

variable "jwt_secret" {
  sensitive = true
}

# Environment-based secrets
# Production: Use cloud secret managers
# Development: Use terraform.tfvars (gitignored)
```

### 2. Network Security
```hcl
# AWS Security Groups
ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]  # Public access
}

ingress {
  from_port       = 8000
  to_port         = 8000
  protocol        = "tcp"
  security_groups = [aws_security_group.alb.id]  # ALB only
}
```

### 3. IAM & Permissions
```hcl
# Minimal required permissions
# AWS: ECS execution role with CloudWatch logs
# GCP: Cloud Run invoker role
# Azure: Container instance contributor
```

## Testing Strategy

### 1. Local Validation
```bash
# Validate Terraform configuration
cd terraform/aws
terraform init
terraform validate
terraform plan

# Test with dry-run
terraform plan -out=tfplan
```

### 2. Environment Testing
```bash
# Development environment
terraform apply -var="environment=development"

# Staging environment
terraform apply -var="environment=staging"

# Production environment
terraform apply -var="environment=production"
```

### 3. Infrastructure Testing
```bash
# Verify deployment
curl https://{load_balancer_dns}/health

# Check logs
aws logs tail /ecs/ninaivalaigal-api --follow  # AWS
gcloud logging read "resource.type=cloud_run_revision"  # GCP
az container logs --resource-group ninaivalaigal-rg --name ninaivalaigal-api  # Azure
```

## Monitoring & Observability

### 1. Infrastructure Metrics
- **Resource utilization** (CPU, memory, network)
- **Cost tracking** per environment
- **Deployment success/failure rates**
- **Infrastructure drift detection**

### 2. Application Metrics
- **Health check status** from load balancers
- **Response times** and error rates
- **Container restart counts**
- **Auto-scaling events**

## Cost Management

### 1. Resource Sizing
```hcl
# Development: Minimal resources
cpu    = "256"
memory = "512"

# Production: Optimized resources
cpu    = "1024"
memory = "2048"
```

### 2. Auto-scaling Configuration
```hcl
# AWS ECS
desired_count = 2
min_capacity  = 1
max_capacity  = 10

# GCP Cloud Run
min_instances = 1
max_instances = 10

# Azure Container Instances
restart_policy = "OnFailure"
```

## Success Criteria

### 1. Functional Requirements
- ✅ Infrastructure deploys successfully on all three cloud providers
- ✅ Applications are accessible via public endpoints
- ✅ Health checks pass consistently
- ✅ Database connectivity works (if enabled)

### 2. Operational Requirements
- ✅ Terraform state is properly managed
- ✅ Infrastructure changes are version controlled
- ✅ Deployments are repeatable and idempotent
- ✅ Cleanup (destroy) works without manual intervention

### 3. Security Requirements
- ✅ Secrets are properly managed (not in code)
- ✅ Network access is appropriately restricted
- ✅ IAM permissions follow least privilege principle
- ✅ Resources are properly tagged for governance

## Future Enhancements

1. **Remote State**: Implement remote state backends for team collaboration
2. **Modules**: Extract reusable Terraform modules
3. **Multi-Environment**: Implement workspace-based environment management
4. **Cost Optimization**: Implement auto-shutdown for development environments
5. **Compliance**: Add compliance scanning and governance policies

## Dependencies

- Terraform >= 1.0
- Cloud provider CLI tools (aws, gcloud, az)
- Appropriate cloud provider credentials
- GitHub Container Registry access for image pulls

This specification ensures ninaivalaigal has professional, repeatable infrastructure deployment capabilities across major cloud providers with proper automation and governance.
