terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "ninaivalaigal" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "ninaivalaigal"
  }
}

# Container Group (Azure Container Instances)
resource "azurerm_container_group" "ninaivalaigal_api" {
  name                = "ninaivalaigal-api"
  location            = azurerm_resource_group.ninaivalaigal.location
  resource_group_name = azurerm_resource_group.ninaivalaigal.name
  ip_address_type     = "Public"
  dns_name_label      = "ninaivalaigal-api-${random_string.dns_suffix.result}"
  os_type             = "Linux"

  container {
    name   = "ninaivalaigal-api"
    image  = "ghcr.io/arunosaur/ninaivalaigal-api:latest"
    cpu    = "1"
    memory = "1.5"

    ports {
      port     = 8000
      protocol = "TCP"
    }

    environment_variables = {
      DATABASE_URL              = var.database_url
      NINAIVALAIGAL_JWT_SECRET = var.jwt_secret
    }

    liveness_probe {
      http_get {
        path   = "/health"
        port   = 8000
        scheme = "Http"
      }
      initial_delay_seconds = 30
      period_seconds        = 10
      failure_threshold     = 3
    }

    readiness_probe {
      http_get {
        path   = "/health"
        port   = 8000
        scheme = "Http"
      }
      initial_delay_seconds = 5
      period_seconds        = 5
      failure_threshold     = 3
    }
  }

  restart_policy = "Always"

  tags = {
    Environment = var.environment
    Project     = "ninaivalaigal"
  }
}

# Random string for DNS name uniqueness
resource "random_string" "dns_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Optional: Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "postgres" {
  count = var.create_database ? 1 : 0

  name                   = "ninaivalaigal-postgres"
  resource_group_name    = azurerm_resource_group.ninaivalaigal.name
  location               = azurerm_resource_group.ninaivalaigal.location
  version                = "15"
  administrator_login    = "nina"
  administrator_password = var.database_password
  zone                   = "1"

  storage_mb = 32768

  sku_name = "B_Standard_B1ms"

  tags = {
    Environment = var.environment
    Project     = "ninaivalaigal"
  }
}

resource "azurerm_postgresql_flexible_server_database" "ninaivalaigal_db" {
  count = var.create_database ? 1 : 0

  name      = "nina"
  server_id = azurerm_postgresql_flexible_server.postgres[0].id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Firewall rule to allow all IPs (for demo purposes)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all" {
  count = var.create_database ? 1 : 0

  name             = "allow-all"
  server_id        = azurerm_postgresql_flexible_server.postgres[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}
