variable "base_project_id" {
  description = "Your existing GCP Default Base Project ID (e.g. My First Project)"
  type        = string
  default     = "YOUR_BASE_PROJECT_ID"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}
