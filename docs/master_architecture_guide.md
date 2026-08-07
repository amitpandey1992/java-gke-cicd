# End-to-End Master System Architecture & Operations Blueprint

This document is the definitive, comprehensive sitemap and architectural blueprint for the **Microservices CI/CD Pipeline, GKE Autopilot Infrastructure, Self-Hosted JFrog Artifactory, and New Relic APM Integration**.

---

## 1. Executive Summary & Master System Architecture

The application is a cloud-native multi-tier system composed of a single-page frontend (Nginx), two Spring Boot microservices (`task-service` and `quote-service`), a PostgreSQL database, a self-hosted JFrog Artifactory repository manager, and New Relic APM telemetry monitoring.

### Master System Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["1. User Access Layer"]
        browser["Web Browser / Client"]
    end

    subgraph StaticIPLayer ["2. GCP Network Exposure"]
        static_ip["GCP Static External IP: 35.232.126.138\n(Permanent Reserved Address)"]
    end

    subgraph GKECluster ["3. Google Kubernetes Engine (Autopilot Mode)"]
        subgraph IngressNginx ["Frontend Tier"]
            fe_pod["frontend Pod (Nginx)\n(Port 80)"]
        end

        subgraph CoreBackend ["Microservices Tier"]
            task_pod["task-service Pod (Spring Boot 3.2.2)\n(Port 8080 + New Relic Agent)"]
            quote_pod["quote-service Pod (Spring Boot 3.2.2)\n(Port 8080 + New Relic Agent)"]
        end

        subgraph DataTier ["Database Tier"]
            db_pod["postgres Pod (PostgreSQL 15)\n(Persistent Volume Claim)"]
        end

        subgraph K8sSecrets ["Kubernetes Security"]
            sec_artifactory["Secret: artifactory-docker-secret"]
            sec_postgres["Secret: postgres-secrets"]
            sec_newrelic["Secret: newrelic-secrets"]
        end
    end

    subgraph ArtifactManagement ["4. Self-Hosted JFrog Artifactory (HTTPS)"]
        art_generic["generic-local\n(newrelic.jar)"]
        art_docker["docker-local\n(task, quote, frontend images)"]
        art_helm["helm-local\n(java-app charts)"]
    end

    subgraph CICDPipeline ["5. CI/CD Build System (GitHub Actions)"]
        github_runner["ubuntu-latest Runner"]
        wif_auth["GCP Workload Identity Federation (WIF)"]
        gradle_jib["Gradle Jib Compiler"]
    end

    subgraph MonitoringCloud ["6. New Relic Cloud"]
        nr_dashboard["New Relic EU APM Collector\n(HTTPS Port 443)"]
    end

    browser -->|http://35.232.126.138| static_ip
    static_ip --> fe_pod
    fe_pod -->|Proxy /api/tasks| task_pod
    fe_pod -->|Proxy /api/quotes| quote_pod
    task_pod -->|JDBC Port 5432| db_pod

    github_runner -->|Keyless OIDC Token| wif_auth
    github_runner -->|Fetch newrelic.jar| art_generic
    github_runner -->|Jib Image Push| art_docker
    sec_artifactory -->|Auth Image Pull| art_docker
    GKECluster -->|Pull Images via Kubelet| art_docker

    task_pod -- "Direct APM Telemetry (JAVA_TOOL_OPTIONS)" --> nr_dashboard
    quote_pod -- "Direct APM Telemetry (JAVA_TOOL_OPTIONS)" --> nr_dashboard
```

---

## 2. Tool Matrix & Component Responsibilities

| Tool / Technology | Category | Primary Function & Responsibilities in System |
|---|---|---|
| **Terraform** | Infrastructure as Code (IaC) | Declaratively provisions GKE Autopilot cluster, GCP Service Accounts, Workload Identity Pools, and IAM bindings. |
| **GKE Autopilot** | Managed Kubernetes | Fully managed serverless Kubernetes cluster. Handles node auto-scaling, OS patching, and pod scheduling. |
| **Google Workload Identity Federation (WIF)** | Cloud Security (OIDC) | Enables keyless authentication between GitHub Actions and GCP using short-lived OpenID Connect tokens. |
| **JFrog Artifactory** | Artifact & Docker Registry | Self-hosted HTTPS registry (`my-jfrog-artifactory.duckdns.org`) storing `newrelic.jar` binaries, Docker images, and Helm charts. |
| **Gradle** | Java Build System | Compiles Java 17 source code, manages project dependencies, and runs unit tests for microservices. |
| **Jib (Google Container Tools)** | Container Compiler | Packages Java applications directly into OCI/Docker container images without requiring a Docker daemon or Dockerfiles. |
| **Docker** | Containerization | Builds Nginx frontend images and manages local image layers. |
| **Helm** | Kubernetes Package Manager | Templates, deploys, and upgrades application manifests (`frontend`, `task-service`, `quote-service`, `postgres`, Secrets). |
| **Nginx** | Reverse Proxy / Frontend | Serves static HTML/JS frontend assets and proxies `/api/tasks` and `/api/quotes` traffic to backend Kubernetes services. |
| **Spring Boot 3.2.2** | Application Framework | Powers `task-service` and `quote-service` microservices with embedded Tomcat and REST APIs. |
| **PostgreSQL 15** | Relational Database | Stores persistent task records for `task-service` backed by Kubernetes PersistentVolumeClaims (PVC). |
| **New Relic Java Agent** | Observability (APM) | Bytecode instrumentation agent (`newrelic.jar`) baked into container images to record response times, DB queries, and errors. |

---

## 3. Infrastructure & Provisioning Layer (Terraform & GCP)

### Terraform Provisioning Architecture

```mermaid
flowchart LR
    subgraph TerraformCode ["Terraform Codebase (terraform/)"]
        tf_main["main.tf / project.tf"]
        tf_gke["gke.tf"]
        tf_wif["wif.tf"]
    end

    subgraph GCPCloud ["Google Cloud Project (project-616fef18-15b8-4d6c-8a2)"]
        gke_cluster["GKE Autopilot Cluster\n(java-gke-cluster / us-central1)"]
        sa["Service Account:\ngithub-actions-deployer"]
        wif_pool["Workload Identity Pool:\ngithub-pool-v5"]
        wif_provider["WIF Provider:\ngithub-provider (OIDC)"]
        static_ip["GCP Compute Address:\nfrontend-static-ip (35.232.126.138)"]
    end

    tf_main --> GCPCloud
    tf_gke --> gke_cluster
    tf_wif --> sa
    tf_wif --> wif_pool
    tf_wif --> wif_provider
```

### Key Terraform Resources Defined:

1. **GKE Autopilot Cluster ([`terraform/gke.tf`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/terraform/gke.tf))**:
   - `google_container_cluster.primary`: Configured with `enable_autopilot = true` in region `us-central1`. GCP manages node provisioning automatically.
2. **Workload Identity Federation ([`terraform/wif.tf`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/terraform/wif.tf))**:
   - `google_service_account.github_actions_sa`: Creates `github-actions-deployer@project-616fef18-15b8-4d6c-8a2.iam.gserviceaccount.com`.
   - `google_iam_workload_identity_pool.github_pool`: Creates pool `github-pool-v5`.
   - `google_iam_workload_identity_pool_provider.github_provider`: Configured with issuer `https://token.actions.githubusercontent.com` and attribute condition restricting access exclusively to repository `amitpandey1992/java-gke-cicd`.
   - IAM Roles Assigned:
     - `roles/container.developer`: Grants permissions to deploy workloads to GKE.
     - `roles/artifactregistry.writer`: Grants artifact creation rights.
3. **Static Reserved IP (GCP Compute API)**:
   - Reserved via `gcloud compute addresses create frontend-static-ip --region us-central1`.
   - Output IP: `35.232.126.138`.

---

## 4. Self-Hosted JFrog Artifactory Repository Taxonomy

To decouple application builds from external vendor network dependencies and bypass GKE Autopilot outbound runtime limits, all assets are centralized in a self-hosted **JFrog Artifactory** instance accessible over SSL (`https://my-jfrog-artifactory.duckdns.org/`).

```mermaid
flowchart TD
    subgraph ArtifactoryInstance ["JFrog Artifactory (my-jfrog-artifactory.duckdns.org)"]
        subgraph GenericRepo ["1. generic-local Repository"]
            nr_jar["path: /newrelic/newrelic.jar\n(40MB New Relic Agent Binary)"]
        end

        subgraph DockerRepo ["2. docker-local Repository"]
            img_fe["image: docker-local/frontend:tag"]
            img_task["image: docker-local/task-service:tag"]
            img_quote["image: docker-local/quote-service:tag"]
        end

        subgraph HelmRepo ["3. helm-local Repository"]
            chart_tgz["chart: java-app-1.0.0.tgz"]
        end
    end
```

---

## 5. CI/CD Build Pipeline & PR-Based Workflow

The deployment workflow ([`.github/workflows/deploy.yml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/.github/workflows/deploy.yml)) follows an Enterprise **Pull-Request (PR) Driven CI/CD Pattern**:

1. **Pull Request (PR Created / Updated):** Triggers **CI Steps** (Source Checkout, Java 17 Setup, and Gradle Unit Tests). Artifacts are NOT pushed to Artifactory and GKE is NOT updated.
2. **Push / Merge to `main` Branch:** Triggers **CD Steps** (WIF Authentication, New Relic fetching, Jib OCI compilation, Artifactory Docker image push, and Helm GKE deployment).

```mermaid
flowchart TD
    subgraph TriggerType ["Trigger Selection"]
        pr_event["1. Pull Request Event (PR to main)"]
        push_event["2. Push / Merge Event (Merge to main)"]
    end

    subgraph CIPipeline ["CI Pipeline (PR Validation)"]
        pr_event --> checkout1[Checkout Code]
        checkout1 --> java_setup1[Setup Java 17]
        java_setup1 --> unit_tests[Run Microservice Unit Tests]
        unit_tests --> pr_success["PR Green Checkmark ✅ (No Deploy)"]
    end

    subgraph CDPipeline ["CD Pipeline (Merge Deployment)"]
        push_event --> checkout2[Checkout Code]
        checkout2 --> wif[GCP WIF OIDC Auth]
        wif --> fetch_nr[Fetch newrelic.jar from Artifactory generic-local]
        fetch_nr --> jib_build[Gradle Jib Build & Layering]
        jib_build --> art_push[Push Images to Artifactory docker-local]
        art_push --> helm_deploy[Helm Upgrade Deploy to GKE]
        helm_deploy --> live_update["Live Production Cluster Updated ✅"]
    end
```

### How Jib Embeds `newrelic.jar` into Image Layers:
Gradle Jib uses a filesystem convention:
```
Runner Directory Path:                     Container File System Path:
─────────────────────────────────────      ─────────────────────────────────
task-service/src/main/jib/             ──▶  /
  └── newrelic/                        ──▶    └── newrelic/
        └── newrelic.jar               ──▶          └── newrelic.jar  ✅
```
During the `./gradlew jib` execution, Jib copies `src/main/jib/newrelic/newrelic.jar` into **Layer 4** of the OCI container image filesystem at `/newrelic/newrelic.jar`.

---

## 6. Kubernetes Pod Scheduling & Secret Management

### Pod Scheduling & Pull Flow

```mermaid
sequenceDiagram
    autonumber
    participant Pipeline as GitHub Actions Workflow
    participant K8s_API as GKE Kubernetes API Server
    participant Secret as K8s Secret (artifactory-docker-secret)
    participant Kubelet as GKE Worker Node Kubelet
    participant Artifactory as Artifactory Docker Registry
    participant Pod as Microservice Pod

    Pipeline->>K8s_API: 1. helm upgrade --install (Passes base64 dockerconfigjson)
    K8s_API->>Secret: 2. Create/Update Secret 'artifactory-docker-secret'
    K8s_API->>Kubelet: 3. Schedule Pod (image: my-jfrog-artifactory.duckdns.org/docker-local/task-service)
    Kubelet->>Secret: 4. Read imagePullSecrets credentials
    Kubelet->>Artifactory: 5. HTTPS Docker Pull (Basic Auth)
    Artifactory-->>Kubelet: 6. Return Pre-baked Image Layers
    Kubelet->>Pod: 7. Start Container & Execute JVM command
```

### Secrets Injected into Kubernetes Namespace:

1. **`artifactory-docker-secret` ([`helm/java-app/templates/artifactory-secret.yaml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/helm/java-app/templates/artifactory-secret.yaml))**:
   - Type: `kubernetes.io/dockerconfigjson`
   - Purpose: Authorizes GKE Kubelet nodes to pull images from `my-jfrog-artifactory.duckdns.org`.
2. **`postgres-secrets` ([`helm/java-app/templates/postgres.yaml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/helm/java-app/templates/postgres.yaml))**:
   - Stores `POSTGRES_PASSWORD`.
3. **`newrelic-secrets` ([`helm/java-app/templates/newrelic-secrets.yaml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/helm/java-app/templates/newrelic-secrets.yaml))**:
   - Stores `license-key` (`NEW_RELIC_LICENSE_KEY`).

---

## 7. Application Topology & End-to-End Request Routing

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant GCP_IP as GCP Reserved Static IP (35.232.126.138)
    participant Nginx_Svc as Frontend Service (Type: LoadBalancer)
    participant Nginx_Pod as Frontend Pod (Nginx Engine)
    participant Task_Svc as Task Service (Kubernetes ClusterIP:8080)
    participant Task_Pod as Task Pod (Spring Boot + New Relic Agent)
    participant DB_Pod as PostgreSQL Database Pod (Port 5432)

    User->>GCP_IP: 1. Send HTTP GET http://35.232.126.138/
    GCP_IP->>Nginx_Svc: 2. Forward to LoadBalancer Service
    Nginx_Svc->>Nginx_Pod: 3. Route to active Nginx Pod (Port 80)
    Nginx_Pod-->>User: 4. Return HTML/JS Static UI Assets

    User->>GCP_IP: 5. User clicks 'Create Task' (POST /api/tasks)
    GCP_IP->>Nginx_Svc: 6. Forward HTTP POST
    Nginx_Svc->>Nginx_Pod: 7. Nginx matches location /api/tasks
    Nginx_Pod->>Task_Svc: 8. Proxy pass to http://task-service:8080/api/tasks
    Task_Svc->>Task_Pod: 9. Route to task-service container
    
    Note over Task_Pod: New Relic Java Agent intercepts controller execution & starts transaction trace
    
    Task_Pod->>DB_Pod: 10. Execute SQL INSERT INTO tasks (JDBC Port 5432)
    DB_Pod-->>Task_Pod: 11. Confirm Transaction Commit
    Task_Pod-->>Nginx_Pod: 12. Return HTTP 200 OK + JSON
    Nginx_Pod-->>User: 13. Render updated Task on UI Screen
```

---

## 8. Observability & Telemetry Architecture (New Relic APM)

```mermaid
flowchart TD
    subgraph PodRuntime ["Microservice Container Pod"]
        jvm_start["JVM Startup command:\njava -javaagent:/newrelic/newrelic.jar -jar app.jar"]
        agent["New Relic Agent Core\n(loaded into JVM memory)"]
        app_code["Spring Boot Controllers & JPA Repositories"]
        
        jvm_start --> agent
        app_code <-->|Bytecode Instrumentation| agent
    end

    subgraph EnvVars ["Environment Variables Passed via Deployment YAML"]
        env1["JAVA_TOOL_OPTIONS: -javaagent:/newrelic/newrelic.jar"]
        env2["NEW_RELIC_APP_NAME: task-service / quote-service"]
        env3["NEW_RELIC_LICENSE_KEY: Loaded from newrelic-secrets"]
    end

    subgraph NRCloud ["New Relic EU Telemetry Cloud"]
        collector["EU Collector Endpoint\n(https://collector.eu01.nr-data.net:443)"]
        apm_dashboard["APM Transaction Dashboard"]
    end

    EnvVars --> jvm_start
    agent -- "Asynchronous Batch Export (HTTPS Port 443)" --> collector
    collector --> apm_dashboard
```

---

## 9. Operations & Maintenance Playbook

### A. Cost Optimization (Zero-Cost Shutdown)
To pause billing when taking a break:
```bash
# 1. Connect to GKE cluster
gcloud container clusters get-credentials java-gke-cluster --region us-central1 --project project-616fef18-15b8-4d6c-8a2

# 2. Uninstall Helm workloads (Stops all Pods & deletes Load Balancers)
helm uninstall java-app
```
* **Billing Impact:** Running pods and Load Balancers drop to 0. GKE Autopilot control plane charges $0 when no pods are executing. The Static IP `35.232.126.138` remains reserved.

### B. Resuming Workloads
Push any commit to GitHub, or execute manually:
```bash
helm upgrade --install java-app ./helm/java-app
```
* **Result:** Workloads deploy and automatically bind back to Static IP `35.232.126.138`.

### C. Useful Verification Commands
```bash
# Check Pod status across cluster
kubectl get pods -o wide

# Check External Load Balancer Static IP binding
kubectl get svc frontend

# View real-time application logs
kubectl logs -l app=task-service --tail=100 -f
kubectl logs -l app=quote-service --tail=100 -f

# Check secret creation
kubectl get secrets
```
