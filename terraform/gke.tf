resource "google_container_cluster" "primary" {
  project  = var.project_id
  name     = var.cluster_name
  location = var.region

  # Enabling GKE Autopilot mode for fully managed, cost-optimized cluster
  enable_autopilot = true

  # Deletion protection disabled for dev/demo purposes
  deletion_protection = false
}

output "gke_cluster_name" {
  description = "The name of the GKE Cluster"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_location" {
  description = "The region of the GKE Cluster"
  value       = google_container_cluster.primary.location
}
