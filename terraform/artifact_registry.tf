resource "google_artifact_registry_repository" "java_app_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repository for Java application container images"
  format        = "DOCKER"
}

output "artifact_registry_url" {
  description = "The URL of the created Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.java_app_repo.repository_id}"
}
