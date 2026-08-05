resource "google_artifact_registry_repository" "java_app_repo" {
  project       = google_project.demo_project.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repository for Java application container images"
  format        = "DOCKER"

  depends_on = [
    google_project_service.artifact_registry_api
  ]
}

