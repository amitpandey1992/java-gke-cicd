output "new_created_project_id" {
  description = "The ID of the newly created GCP Project"
  value       = google_project.demo_project.project_id
}

output "artifact_registry_url" {
  description = "The Artifact Registry Docker Repository URL"
  value       = "${var.region}-docker.pkg.dev/${google_project.demo_project.project_id}/${google_artifact_registry_repository.java_app_repo.repository_id}"
}

output "gke_cluster_name" {
  description = "The name of the GKE cluster"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_location" {
  description = "The region of the GKE Cluster"
  value       = google_container_cluster.primary.location
}


output "workload_identity_provider" {
  description = "COPY THIS VALUE TO GITHUB SECRET: WIF_PROVIDER"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "service_account_email" {
  description = "COPY THIS VALUE TO GITHUB SECRET: WIF_SERVICE_ACCOUNT"
  value       = google_service_account.github_actions_sa.email
}
