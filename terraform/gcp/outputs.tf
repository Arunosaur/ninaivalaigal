output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.ninaivalaigal_api.status[0].url
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.ninaivalaigal_api.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = var.create_database ? google_sql_database_instance.postgres[0].connection_name : null
}

output "database_ip" {
  description = "Cloud SQL instance IP"
  value       = var.create_database ? google_sql_database_instance.postgres[0].public_ip_address : null
}
