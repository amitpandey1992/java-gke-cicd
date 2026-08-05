variable "billing_account_id" {
  description = "Your GCP Billing Account ID (from GCP Console -> Billing)"
  type        = string
  sensitive   = true # Prevents Terraform from logging this value in CLI output
}

variable "new_project_id" {
  description = "The unique GCP Project ID for the new project to be created"
  type        = string
  default     = "java-gke-demo-proj-2026"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
  default     = "java-gke-cluster"
}

variable "artifact_repo_name" {
  description = "The name of the Artifact Registry repository"
  type        = string
  default     = "java-app-repo"
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo for Workload Identity Federation"
  type        = string
  default     = "your-username/java-gke-cicd"
}
