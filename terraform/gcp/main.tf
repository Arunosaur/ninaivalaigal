terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run Service
resource "google_cloud_run_service" "ninaivalaigal_api" {
  name     = "ninaivalaigal-api"
  location = var.region

  template {
    spec {
      containers {
        image = "ghcr.io/arunosaur/ninaivalaigal-api:latest"

        ports {
          container_port = 8000
        }

        env {
          name  = "DATABASE_URL"
          value = var.database_url
        }

        env {
          name  = "NINAIVALAIGAL_JWT_SECRET"
          value = var.jwt_secret
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 30
          period_seconds        = 10
        }

        readiness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 5
          period_seconds        = 5
        }
      }

      container_concurrency = 100
      timeout_seconds      = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.cloud_run_api]
}

# IAM policy to allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  service  = google_cloud_run_service.ninaivalaigal_api.name
  location = google_cloud_run_service.ninaivalaigal_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Enable required APIs
resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"

  disable_dependent_services = true
}

resource "google_project_service" "container_registry_api" {
  service = "containerregistry.googleapis.com"

  disable_dependent_services = true
}

# Cloud SQL PostgreSQL instance (optional)
resource "google_sql_database_instance" "postgres" {
  count = var.create_database ? 1 : 0

  name             = "ninaivalaigal-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        value = "0.0.0.0/0"
        name  = "all"
      }
    }

    database_flags {
      name  = "shared_preload_libraries"
      value = "vector"
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "ninaivalaigal_db" {
  count = var.create_database ? 1 : 0

  name     = "nina"
  instance = google_sql_database_instance.postgres[0].name
}

resource "google_sql_user" "ninaivalaigal_user" {
  count = var.create_database ? 1 : 0

  name     = "nina"
  instance = google_sql_database_instance.postgres[0].name
  password = var.database_password
}
