# Simple Project ID variable for direct provisioning
variable "project_id" {
  description = "Your active GCP Project ID"
  type        = string
  default     = "project-616fef18-15b8-4d6c-8a2"
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
