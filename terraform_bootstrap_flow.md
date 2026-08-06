# 🗺️ Terraform Bootstrap & Execution Workflows

This guide visualizes the differences between running Terraform locally on your workstation versus automating it using Terraform Cloud (TFC) with keyless Workload Identity Federation (WIF).

---

## 💻 Workflow 1: Running Root Terraform Locally

If you just run Terraform directly from your terminal, the bootstrap folder is **not used**.

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant Laptop as Local Station
    participant GCP as Google Cloud Platform

    Developer->>Laptop: Run: gcloud auth login
    Laptop->>GCP: Authenticates User Account
    GCP-->>Laptop: Stores user credentials in local config

    Developer->>Laptop: Run: gcloud auth application-default login
    Laptop-->>Laptop: Creates Application Default Credentials (ADC) JSON file

    Developer->>Laptop: Run: cd terraform && terraform apply
    Laptop->>GCP: Resolves resources using local ADC credentials
    Note over GCP: Provisions Project, GKE Autopilot,<br/>Artifact Registry, and GitHub WIF
    GCP-->>Laptop: Success!
```

---

## ☁️ Workflow 2: Running Root Terraform on Terraform Cloud

If you want to use **Terraform Cloud** to run the root `terraform/` templates automatically, you must run the **bootstrap** configuration once locally first.

### Phase A: Setup the Bootstrap (Once from Local Station)
We create a bridge (trust association) between GCP and Terraform Cloud.

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant Laptop as Local Station
    participant GCP as Google Cloud Platform

    Developer->>Laptop: Run: cd terraform/bootstrap && terraform apply
    Laptop->>GCP: Creates tfc-bootstrap-sa (Service Account)
    Laptop->>GCP: Creates tfc-pool & tfc-provider (WIF Pool)
    Note over GCP: Trust policy configured for<br/>"https://app.terraform.io"
    GCP-->>Laptop: Returns TFC_GCP_WORKLOAD_POOL_ID & SA email
```

### Phase B: Configure TFC Variables (Once in Terraform Cloud Console)
You copy the output values from Phase A and save them in your Terraform Cloud Workspace settings.

```
[Terraform Cloud Workspace Variables]
 ├── TFC_GCP_WORKLOAD_POOL_ID = "projects/12345/locations/global/workloadIdentityPools/tfc-pool/providers/tfc-provider"
 └── TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL = "tfc-bootstrap-sa@project-id.iam.gserviceaccount.com"
```

### Phase C: Automated Execution (Runs on Git Push)
Whenever you push changes to your root `terraform/` infrastructure code, Terraform Cloud runs it automatically without any passwords.

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant Git as GitHub / Git Commit
    participant TFC as Terraform Cloud Runner
    participant GCP as Google Cloud Platform

    Developer->>Git: git push
    Git->>TFC: Triggers Workspace Run
    TFC->>GCP: 1. Sends OIDC Identity Token (Signed by TFC)
    Note over GCP: GCP WIF validates TFC token signature<br/>and matches with TFC_GCP_WORKLOAD_POOL_ID
    GCP-->>TFC: 2. Issues temporary Access Token for tfc-bootstrap-sa
    TFC->>GCP: 3. Runs "terraform apply" for root templates
    Note over GCP: Provisions Project, GKE Cluster,<br/>Artifact Registry, and GitHub WIF
    GCP-->>TFC: Infrastructure created!
```
