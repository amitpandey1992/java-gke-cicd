# Service Account for GitHub Actions Pipeline
resource "google_service_account" "github_actions_sa" {
  project      = var.project_id
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer Service Account"
}

# Grant Artifact Registry Writer role to Service Account
resource "google_project_iam_member" "artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Grant GKE Developer role to Service Account
resource "google_project_iam_member" "gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Workload Identity Pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool-v5"
  display_name              = "GitHub Actions WIF Pool"
  description               = "Identity pool for GitHub Actions pipelines"
}

# OIDC Provider for GitHub Actions
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

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

# Fetch project metadata to get the project number dynamically
data "google_project" "project" {
  project_id = var.project_id
}

# Grant Artifact Registry Reader to the default Compute Engine service account used by GKE nodes
resource "google_project_iam_member" "gke_node_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}
