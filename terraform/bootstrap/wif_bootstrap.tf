terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.15.0"
    }
  }
}

provider "google" {
  project = var.base_project_id
  region  = var.region
}

# Service Account for Terraform Cloud to create new projects and resources
resource "google_service_account" "tfc_sa" {
  account_id   = "tfc-bootstrap-sa"
  display_name = "Terraform Cloud Bootstrap Service Account"
}

# Grant Project Creator role so TFC can create new GCP Projects
resource "google_project_iam_member" "project_creator" {
  project = var.base_project_id
  role    = "roles/resourcemanager.projectCreator"
  member  = "serviceAccount:${google_service_account.tfc_sa.email}"
}

# Grant Billing User role so TFC can link billing to newly created projects
resource "google_project_iam_member" "billing_user" {
  project = var.base_project_id
  role    = "roles/billing.user"
  member  = "serviceAccount:${google_service_account.tfc_sa.email}"
}

# Workload Identity Pool for Terraform Cloud
resource "google_iam_workload_identity_pool" "tfc_pool" {
  workload_identity_pool_id = "tfc-pool"
  display_name              = "Terraform Cloud WIF Pool"
  description               = "Identity pool for Terraform Cloud runs"
}

# OIDC Provider trusting https://app.terraform.io
resource "google_iam_workload_identity_pool_provider" "tfc_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.tfc_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "tfc-provider"
  display_name                       = "Terraform Cloud OIDC Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.aud"        = "assertion.aud"
    "attribute.terraform_workspace_id"   = "assertion.terraform_workspace_id"
    "attribute.terraform_organization_id" = "assertion.terraform_organization_id"
  }

  oidc {
    issuer_uri = "https://app.terraform.io"
  }
}

# IAM Binding allowing Terraform Cloud to impersonate the Bootstrap SA
resource "google_service_account_iam_member" "tfc_wif_impersonation" {
  service_account_id = google_service_account.tfc_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.tfc_pool.name}/*"
}
