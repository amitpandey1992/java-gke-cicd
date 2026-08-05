# Create a Brand New GCP Project using Terraform
resource "google_project" "demo_project" {
  name            = "Java GKE Demo Project"
  project_id      = var.new_project_id
  billing_account = var.billing_account_id
}

# Enable required GCP Service APIs automatically
resource "google_project_service" "gke_api" {
  project                    = google_project.demo_project.project_id
  service                    = "container.googleapis.com"
  disable_on_destroy         = false
}

resource "google_project_service" "artifact_registry_api" {
  project                    = google_project.demo_project.project_id
  service                    = "artifactregistry.googleapis.com"
  disable_on_destroy         = false
}

resource "google_project_service" "iam_api" {
  project                    = google_project.demo_project.project_id
  service                    = "iam.googleapis.com"
  disable_on_destroy         = false
}

resource "google_project_service" "iam_credentials_api" {
  project                    = google_project.demo_project.project_id
  service                    = "iamcredentials.googleapis.com"
  disable_on_destroy         = false
}

