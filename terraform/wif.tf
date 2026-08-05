# Service Account for GitHub Actions Pipeline
resource "google_service_account" "github_actions_sa" {
  project      = google_project.demo_project.project_id
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer Service Account"

  depends_on = [
    google_project_service.iam_api
  ]
}

# Grant Artifact Registry Writer role to Service Account
resource "google_project_iam_member" "artifact_registry_writer" {
  project = google_project.demo_project.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Grant GKE Developer role to Service Account
resource "google_project_iam_member" "gke_developer" {
  project = google_project.demo_project.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Workload Identity Pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = google_project.demo_project.project_id
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions WIF Pool"
  description               = "Identity pool for GitHub Actions pipelines"

  depends_on = [
    google_project_service.iam_credentials_api
  ]
}

# OIDC Provider for GitHub Actions
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = google_project.demo_project.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# IAM Binding allowing GitHub Actions from specific repo to impersonate the Service Account
resource "google_service_account_iam_member" "github_wif_impersonation" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}
