variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "ninaivalaigal-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
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

variable "create_database" {
  description = "Create Azure Database for PostgreSQL"
  type        = bool
  default     = false
}

variable "database_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
  default     = "change_me_securely"
}

variable "subscription_id" {
  description = "Azure subscription ID for budget alerts"
  type        = string
  default     = ""
}

variable "budget_amount" {
  description = "Monthly budget amount in USD"
  type        = number
  default     = 100
}

variable "budget_alert_emails" {
  description = "Email addresses for budget alerts"
  type        = list(string)
  default     = []
}
