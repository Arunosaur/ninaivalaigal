variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
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

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = true
}

variable "create_database" {
  description = "Create Cloud SQL PostgreSQL database"
  type        = bool
  default     = false
}

variable "database_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
  default     = "change_me_securely"
}
