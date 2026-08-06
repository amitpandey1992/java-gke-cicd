output "tfc_gcp_workload_pool_id" {
  description = "Copy to Terraform Cloud Environment Variable: TFC_GCP_WORKLOAD_POOL_ID"
  value       = google_iam_workload_identity_pool_provider.tfc_provider.name
}

output "tfc_gcp_run_service_account_email" {
  description = "Copy to Terraform Cloud Environment Variable: TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL"
  value       = google_service_account.tfc_sa.email
}
