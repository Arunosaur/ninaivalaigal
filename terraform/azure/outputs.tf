output "container_group_fqdn" {
  description = "FQDN of the container group"
  value       = azurerm_container_group.ninaivalaigal_api.fqdn
}

output "container_group_ip" {
  description = "Public IP of the container group"
  value       = azurerm_container_group.ninaivalaigal_api.ip_address
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.ninaivalaigal.name
}

output "database_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = var.create_database ? azurerm_postgresql_flexible_server.postgres[0].fqdn : null
}
