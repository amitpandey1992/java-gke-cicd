# Senior DevOps & Cloud Architect Interview Q&A (100 Scenario-Based Questions)

This document contains **100 production-grounded, scenario-based interview questions and quick answers** tailored for a **Senior DevOps / Lead SRE / Cloud Architect (13+ Years Experience)**. All scenarios, troubleshooting cases, architectural trade-offs, and solutions are derived directly from our end-to-end **Java Microservices GKE CI/CD & Observability Project**.

---

## Section 1: GKE Autopilot & GCP Infrastructure Architecture (Q1 – Q10)

### Q1: Why did you choose GKE Autopilot over GKE Standard for this microservices architecture?
**Answer:** GKE Autopilot provides a fully managed, zero-node-management Kubernetes environment where Google manages node provisioning, OS patching, auto-scaling, and security hardening. In Autopilot, billing is based strictly on requested Pod CPU/RAM rather than underlying Compute Engine VM capacity. When workloads are scaled down or uninstalled (`helm uninstall`), resource consumption drops to zero, eliminating idle node costs while maintaining enterprise SLAs.

### Q2: What network or OS-level constraints does GKE Autopilot impose on pods?
**Answer:** GKE Autopilot enforces strict node-level security boundaries:
1. No root access or privileged containers (`privileged: true`).
2. Custom Linux kernel parameters or `containerd` config mutations (like `insecure_registries`) are prohibited.
3. Outbound runtime internet egress from Pods without Cloud NAT or Public IPs is blocked by default, causing runtime HTTP downloads (`wget`/`curl`) inside containers or initContainers to fail with `Connection reset by peer`.

### Q3: How do you achieve zero-cost shutdown in GKE Autopilot without losing your reserved network endpoints?
**Answer:** Execute `helm uninstall java-app`. In GKE Autopilot, removing all workload Pods and Load Balancers drops active Pod CPU/RAM billing to $0. Because the GCP Static External IP (`35.232.126.138`) is reserved independently via GCP Compute API (`gcloud compute addresses create`), the IP remains assigned to your GCP account. Re-deploying via `helm upgrade --install` instantly re-binds the workloads to the exact same IP.

### Q4: How does pod autoscaling work in GKE Autopilot compared to standard clusters?
**Answer:** In GKE Standard, Cluster Autoscaler provisions Compute Engine VMs first, and then Kubernetes schedules Pods onto those VMs. In GKE Autopilot, you request Pod CPU/Memory limits, and GKE automatically handles node capacity provisioning under the hood transparently. Horizontal Pod Autoscaler (HPA) scales Pod replicas based on CPU/RAM metrics without needing node pool sizing policies.

### Q5: In GKE Autopilot, why did runtime `initContainers` fail when trying to download `newrelic.jar` from public URLs?
**Answer:** GKE Autopilot pods run in private VPC subnets by default without external public IP addresses on node interfaces. Without Cloud NAT configured for outbound internet egress, `initContainers` attempting runtime HTTP/HTTPS downloads experience TCP connection drops (`Connection reset by peer`). The solution is to pre-bake binaries during CI/CD build time using Gradle Jib.

### Q6: How do you handle regional resiliency versus zonal cost trade-offs in GKE?
**Answer:** A regional GKE cluster deploys control plane replicas across three availability zones within a region (e.g., `us-central1-a`, `us-central1-b`, `us-central1-c`), providing high availability against zonal outages. For dev/demo environments, regional Autopilot clusters ensure high availability while Pod billing remains tied to requested Pod replicas rather than per-zone node overhead.

### Q7: What happens to a GKE ClusterIP service if all backend pods crash?
**Answer:** The ClusterIP service remains active in the Kubernetes API server and IP Virtual Server (IPVS) / iptables routing rules. However, because there are no healthy Pod endpoints behind the Service selector, any incoming connection requests to the ClusterIP will timeout or return `503 Service Unavailable` / `Connection Refused` at the Nginx reverse proxy level.

### Q8: What is the difference between GKE Node Service Account and Workload Service Account?
**Answer:** The GKE Node Service Account is assigned to the underlying Compute Engine VM nodes (used for pulling system images, logging, and monitoring). The Workload Service Account (via Workload Identity) is bound to specific Kubernetes Service Accounts (KSA) inside Pods to grant fine-grained GCP IAM permissions (e.g., accessing Secret Manager or Cloud Storage) without sharing node-level credentials.

### Q9: How do you optimize container image pulling speed in GKE Autopilot?
**Answer:** Use minimal base images (e.g., `alpine` or distroless), leverage Jib layer caching (separating dependencies from application code), host container images in a geographically co-located private registry (e.g., Artifactory or Artifact Registry in `us-central1`), and set `imagePullPolicy: IfNotPresent`.

### Q10: How do you troubleshoot a Pod stuck in `ImagePullBackOff` on GKE Autopilot?
**Answer:** Run `kubectl describe pod <pod-name>`. Inspect the `Events` section at the bottom. Common root causes include:
1. Missing `imagePullSecrets` in Deployment manifest.
2. Insecure registry TLS mismatch (`http://` instead of `https://`).
3. Expired or invalid Docker registry credentials in `kubernetes.io/dockerconfigjson`.
4. Typo in image repository path or tag.

---

## Section 2: Terraform & Infrastructure as Code (Q11 – Q20)

### Q11: How did you structure your Terraform module for GKE and IAM provisioning?
**Answer:** Modularized by responsibility:
- `main.tf` / `project.tf`: Provider configuration and project metadata.
- `gke.tf`: Declarative definition of `google_container_cluster.primary` with `enable_autopilot = true`.
- `wif.tf`: Identity management including `google_service_account`, `google_iam_workload_identity_pool`, `google_iam_workload_identity_pool_provider`, and IAM policy bindings.
- `variables.tf` / `terraform.tfvars`: Parameterized project ID, region, and GitHub repository constraints.

### Q12: Why is `deletion_protection = false` set in `gke.tf` for development environments?
**Answer:** By default, Google Terraform Provider enables deletion protection on GKE clusters to prevent accidental infrastructure destruction. Setting `deletion_protection = false` allows clean automated teardown via `terraform destroy` during CI/CD cleanup testing without manual GCP console intervention.

### Q13: How does Terraform manage GCP IAM member bindings (`google_project_iam_member` vs `google_project_iam_binding`)?
**Answer:** `google_project_iam_member` is non-authoritative; it appends a specific IAM role to a single identity without altering other existing members of that role. `google_project_iam_binding` is authoritative; it overwrites the entire member list for that role, which can accidentally revoke access for other service accounts. We used `google_project_iam_member` for safety.

### Q14: How do you prevent sensitive Terraform output variables (like tokens or private keys) from leaking in logs?
**Answer:** Mark the output variable with `sensitive = true` in `outputs.tf`. This instructs Terraform CLI to redact the value as `(sensitive value)` in stdout and plan/apply logs. Additionally, store state files securely in a remote GCP Cloud Storage (GCS) backend with bucket encryption and restricted IAM access.

### Q15: What is the purpose of `attribute_condition` in Terraform `google_iam_workload_identity_pool_provider`?
**Answer:** `attribute_condition` enforces strict security boundaries on incoming OpenID Connect (OIDC) assertions. Setting `attribute_condition = "assertion.repository == 'amitpandey1992/java-gke-cicd'"` ensures that only workflows originating from that specific GitHub repository can exchange OIDC tokens for GCP IAM access, preventing unauthorized GitHub repositories from impersonating your Service Account.

### Q16: How do you handle Terraform state locking in a multi-developer CI/CD environment?
**Answer:** Configure a GCS backend in `main.tf` (`backend "gcs" { bucket = "my-tf-state-bucket" }`). GCP Cloud Storage natively supports automatic state locking via GCS object hold/lease mechanisms, preventing race conditions or state corruption when multiple pipelines or developers run `terraform apply` simultaneously.

### Q17: What is the difference between `google_service_account_iam_member` and `google_project_iam_member`?
**Answer:** `google_project_iam_member` grants project-wide permissions (e.g., `roles/container.developer` across the GCP Project). `google_service_account_iam_member` grants resource-level permissions on the Service Account itself (e.g., allowing GitHub WIF PrincipalSet to assume `roles/iam.workloadIdentityUser` on `github-actions-deployer`).

### Q18: How do you pass dynamic outputs from Terraform into a GitHub Actions pipeline?
**Answer:** Define explicit outputs in `outputs.tf` (e.g., `workload_identity_provider` string). In GitHub Actions, run `terraform output -raw workload_identity_provider` and write it to `$GITHUB_ENV` or `$GITHUB_OUTPUT` for downstream pipeline steps.

### Q19: Why is `data "google_project" "project"` used in Terraform?
**Answer:** The data source fetches dynamic GCP project metadata (such as the numeric `project_number`). This is required to construct system service account email addresses programmatically, such as the default Compute Engine service account (`<project_number>-compute@developer.gserviceaccount.com`).

### Q20: How do you drift-correct infrastructure provisioned by Terraform?
**Answer:** Run `terraform plan`. Terraform compares the real-world GCP resource state (via GCP APIs) against the state file and code. If manual changes were made (e.g., someone altered GKE settings via console), `terraform plan` flags the drift and `terraform apply` restores the declared state.

---

## Section 3: Workload Identity Federation (WIF) & Keyless OIDC (Q21 – Q30)

### Q21: What is Workload Identity Federation (WIF) and why is it preferred over Service Account JSON keys?
**Answer:** WIF eliminates long-lived Service Account JSON keys. Storing static JSON keys in GitHub Secrets poses security risks (key leaks, lack of rotation). WIF establishes an OIDC trust relationship between GitHub and GCP. GitHub Actions requests a short-lived (1-hour) federated token from GCP for each pipeline run, enforcing zero-trust credential hygiene.

### Q22: Explain the step-by-step token exchange mechanism in GitHub WIF authentication.
**Answer:**
1. GitHub Actions runner requests an OIDC JWT token from GitHub's OIDC provider containing claims (`repo`, `actor`, `sha`).
2. Runner sends the JWT token to GCP Security Token Service (STS) endpoint.
3. GCP STS validates the signature against `https://token.actions.githubusercontent.com` and checks `attribute_mapping` & `attribute_condition`.
4. STS issues a short-lived GCP Federated Token.
5. Runner calls GCP IAM Credentials API to impersonate `github-actions-deployer` Service Account, obtaining a temporary GCP OAuth2 access token.

### Q23: What attribute mappings are required for GitHub Actions in `google_iam_workload_identity_pool_provider`?
**Answer:**
```hcl
attribute_mapping = {
  "google.subject"       = "assertion.sub"
  "attribute.actor"      = "assertion.actor"
  "attribute.repository" = "assertion.repository"
}
```
This maps GitHub OIDC JWT claim assertions to GCP security attributes for IAM evaluation.

### Q24: What IAM role is required to allow WIF impersonation on a Service Account?
**Answer:** `roles/iam.workloadIdentityUser`. The principal binding format is:
`principalSet://iam.googleapis.com/projects/<PROJECT_NUM>/locations/global/workloadIdentityPools/<POOL_ID>/attribute.repository/<GITHUB_REPO>`

### Q25: How do you configure `google-github-actions/auth@v2` in a GitHub Actions workflow file?
**Answer:**
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/12345/locations/global/workloadIdentityPools/github-pool-v5/providers/github-provider'
    service_account: 'github-actions-deployer@project-id.iam.gserviceaccount.com'
```

### Q26: What happens if `permissions: id-token: write` is missing in the GitHub Actions workflow?
**Answer:** The workflow step fails with `OIDC provider token request failed`. GitHub Actions requires explicit `id-token: write` workflow permissions to allow the runner to request the initial OIDC JWT bearer token from GitHub's internal token service.

### Q27: How do you restrict WIF authentication to only the `main` branch of a repository?
**Answer:** Update `attribute_condition` in Terraform to check the reference claim:
`attribute_condition = "assertion.repository == 'owner/repo' && assertion.ref == 'refs/heads/main'"`

### Q28: Can WIF be used to authenticate with non-GCP services?
**Answer:** WIF is a GCP feature for external workloads. However, the underlying standard (OIDC / OAuth2 Subject Token Exchange - RFC 8693) is universally used across AWS (IAM Roles for Service Accounts), Azure (Managed Identities), and HashiCorp Vault.

### Q29: How do you debug WIF authentication failure `403 Forbidden: Principal unable to impersonate service account`?
**Answer:**
1. Check project number in the `principalSet` string.
2. Verify exact string match for `attribute.repository` (case-sensitive `owner/repo`).
3. Ensure `roles/iam.workloadIdentityUser` is granted on the target Service Account.
4. Verify IAM propagation delay (can take 60 seconds after Terraform creation).

### Q30: What is the lifespan of an access token generated via WIF?
**Answer:** By default, 1 hour (3,600 seconds). It can be configured up to a maximum of 12 hours if required for long-running pipelines using service account token lifetime settings.

---

## Section 4: JFrog Artifactory, TLS & Registry Security (Q31 – Q40)

### Q31: Why did GKE Kubelet fail to pull images when Artifactory was accessed via HTTP IP (`137.23.52.82:8082`)?
**Answer:** GKE Kubelet and container runtime (`containerd`) strictly enforce HTTPS/TLS for remote container registries. When configured with plain HTTP, `containerd` returns `http: server gave HTTP response to HTTPS client` or `ErrImagePull`. In GKE Autopilot, system OS files (`/etc/containerd/config.toml`) cannot be modified to add `insecure_registries`, making HTTPS mandatory.

### Q32: How did you resolve the Docker CLI TLS error `remote error: tls: unrecognized name` during Artifactory login?
**Answer:** The error occurs when accessing an IP address over TLS without Server Name Indication (SNI) matching the SSL certificate SAN. The solution was migrating from plain IP to a valid SSL-enabled FQDN domain (`my-jfrog-artifactory.duckdns.org`) backed by a valid TLS certificate.

### Q33: Describe the repository structure setup in JFrog Artifactory for this project.
**Answer:**
1. **`generic-local`**: Stores generic binary dependencies (`newrelic.jar`).
2. **`docker-local`**: OCI/Docker registry repository storing microservice container images (`task-service`, `quote-service`, `frontend`).
3. **`helm-local`**: Helm chart repository for packaged Kubernetes charts.

### Q34: How do GKE Pods authenticate with a private Artifactory Docker registry?
**Answer:**
1. CI/CD pipeline generates a base64-encoded `dockerconfigjson` credential using Artifactory API tokens.
2. Helm deploys `artifactory-docker-secret` (`type: kubernetes.io/dockerconfigjson`) into the Kubernetes namespace.
3. Workload Deployment manifests include `imagePullSecrets: [{name: artifactory-docker-secret}]`.
4. GKE Kubelet reads the secret to authenticate with `my-jfrog-artifactory.duckdns.org` during image pull.

### Q35: How did you implement dynamic build-time fetching and auto-upload of `newrelic.jar` to Artifactory?
**Answer:** In `.github/workflows/deploy.yml`, the runner executes a `curl` check against Artifactory `generic-local`:
- If HTTP 200: Downloads `newrelic.jar` from Artifactory `generic-local`.
- If HTTP 404: Downloads official `newrelic.jar` from New Relic's CDN and uploads (`curl -T`) it to Artifactory `generic-local` using `ARTIFACTORY_GENERIC_TOKEN`, caching it for future builds.

### Q36: Why is storing 40MB `.jar` binaries directly in Git considered an anti-pattern?
**Answer:** Git is designed for text delta tracking. Committing large binary files bloats `.git` repository size, slows down `git clone` and `git pull` for all developers, causes merge conflicts, and violates enterprise binary management policies. Binaries belong in an Artifact Repository (Artifactory/Nexus).

### Q37: What is an Artifactory Scoped Token and why use it instead of admin passwords?
**Answer:** Scoped Access Tokens allow granting least-privilege, path-restricted, and time-bound permissions (e.g., read/write access limited strictly to `docker-local` or `generic-local`). If leaked, a scoped token limits damage and can be revoked independently without compromising admin credentials.

### Q38: How do you construct a Kubernetes `kubernetes.io/dockerconfigjson` secret programmatically in Helm?
**Answer:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: artifactory-docker-secret
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: {{ .Values.artifactory.dockerConfigJson }}
```
The value is constructed in CI/CD by base64-encoding a JSON string containing the registry hostname, username, and token.

### Q39: What is the difference between Virtual, Local, and Remote repositories in Artifactory?
**Answer:**
- **Local:** Physical repository hosted in Artifactory storing internal artifacts.
- **Remote:** Proxy repository caching artifacts from public registries (e.g., Maven Central, Docker Hub).
- **Virtual:** Aggregated logical endpoint combining Local and Remote repositories under a single URL.

### Q40: How do you clear corrupt image pull credentials cached on a GKE node?
**Answer:** In GKE Autopilot, nodes automatically garbage collect unused images and credentials. To force immediate update, update the secret in Kubernetes (`kubectl create secret docker-registry ... --dry-run=client -o yaml | kubectl apply -f -`) and trigger a rolling update of the Deployment (`kubectl rollout restart deployment <name>`).

---

## Section 5: Gradle Jib, Layering & JVM Agent Pre-Baking (Q41 – Q50)

### Q41: What is Google Container Tools Jib and how does it differ from standard Docker builds?
**Answer:** Jib builds OCI-compliant container images directly from Java build tools (Gradle/Maven) without requiring a Docker daemon, Dockerfiles, or elevated root privileges. Jib separates application bytecode, resources, and dependencies into distinct layer caches, making builds significantly faster and reproducible.

### Q42: Explain the Jib directory convention for copying files into container images.
**Answer:** Jib adheres to a strict filesystem mapping rule:
**"Any file or directory placed under `src/main/jib/` in the source repository is copied directly to the container root `/` directory with identical structure and permissions."**
For example, `task-service/src/main/jib/newrelic/newrelic.jar` is placed at `/newrelic/newrelic.jar` inside the container.

### Q43: How does Jib optimize Docker layer caching for Spring Boot microservices?
**Answer:** Standard Docker builds invalidate all layers after a code change. Jib splits Java applications into granular layers:
1. Dependencies (rarely change).
2. Resources (`application.properties`).
3. Classes (changes frequently).
4. Extra Files (`src/main/jib/`).
When source code changes, Jib only rebuilds and pushes the small Classes layer (~50KB), skipping multi-megabyte dependency pushes.

### Q44: How did you configure Jib in `build.gradle` for task-service?
**Answer:**
```groovy
jib {
    from {
        image = 'eclipse-temurin:17-jre-alpine'
    }
    to {
        image = 'my-jfrog-artifactory.duckdns.org/docker-local/task-service'
        tags = ['latest', project.version]
    }
    container {
        mainClass = 'com.example.demo.DemoApplication'
        ports = ['8080']
        creationTime = 'USE_CURRENT_TIMESTAMP'
    }
}
```

### Q45: How is the New Relic Java Agent activated inside the container without changing `.java` source code?
**Answer:** Kubernetes passes the standard JVM environment variable `JAVA_TOOL_OPTIONS="-javaagent:/newrelic/newrelic.jar"` in the Deployment manifest. On container startup, the Java Virtual Machine automatically detects `JAVA_TOOL_OPTIONS`, loads the agent JAR, and instruments bytecode before executing the main application class.

### Q46: How do you pass authentication credentials to Jib in a CI/CD CLI command?
**Answer:** Pass System Properties to the Gradle execution:
```bash
./gradlew jib \
  -Djib.to.image=${DOCKER_REPO}/task-service:${SHA} \
  -Djib.to.auth.username=${ARTIFACTORY_USER} \
  -Djib.to.auth.password=${ARTIFACTORY_DOCKER_TOKEN}
```

### Q47: Why is `creationTime = 'USE_CURRENT_TIMESTAMP'` used in Jib configuration?
**Answer:** By default, Jib sets image creation timestamps to Epoch 0 (Jan 1, 1970) for build reproducibility. Setting `USE_CURRENT_TIMESTAMP` stamps images with the actual build time, allowing container security scanners and Kubernetes registries to correctly display image age.

### Q48: How do you debug Jib image build failures in CI/CD?
**Answer:** Run Gradle with the info or debug flag (`./gradlew jib --info` or `--debug`). Inspect network HTTP requests to the target registry to identify authentication 401/403 errors, SSL handshake failures, or missing base image layers.

### Q49: What base image was selected for microservices and why?
**Answer:** `eclipse-temurin:17-jre-alpine`. It provides an officially supported OpenJDK 17 Java Runtime Environment on Alpine Linux, keeping container image sizes small (~160MB), reducing attack surface, and eliminating unused development tools (like `javac`).

### Q50: Can Jib build multi-architecture container images (e.g., `amd64` and `arm64`)?
**Answer:** Yes. Jib supports multi-architecture builds via configuration in `build.gradle`:
```groovy
jib.from.platforms {
    platform { architecture = 'amd64'; os = 'linux' }
    platform { architecture = 'arm64'; os = 'linux' }
}
```

---

## Section 6: Kubernetes Networking, Static IP & Nginx Reverse Proxy (Q51 – Q60)

### Q51: How does assigning a GCP Static External IP (`spec.loadBalancerIP`) differ from default LoadBalancer allocation?
**Answer:** Default `type: LoadBalancer` requests a temporary (ephemeral) IP from GCP's free pool. Uninstalling the Helm release destroys the LoadBalancer and releases the IP. Reserving a Static IP (`gcloud compute addresses create frontend-static-ip`) and specifying `loadBalancerIP: "35.232.126.138"` forces GCP Cloud Controller Manager to bind the External Network Load Balancer to that exact reserved IP permanently across all re-installations.

### Q52: How did you implement conditional Static IP binding in Helm templates?
**Answer:** In [`frontend.yaml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/helm/java-app/templates/frontend.yaml):
```yaml
spec:
  type: LoadBalancer
  {{- if .Values.frontend.loadBalancerIP }}
  loadBalancerIP: {{ .Values.frontend.loadBalancerIP | quote }}
  {{- end }}
```
If `.Values.frontend.loadBalancerIP` is provided via CI/CD `--set`, Helm renders `loadBalancerIP`. If empty, Kubernetes falls back to dynamic ephemeral allocation.

### Q53: Explain the role of Nginx as a reverse proxy in this microservices setup.
**Answer:** Nginx acts as the Single Entry Point (API Gateway) for the application:
1. Serves static single-page UI assets (HTML/CSS/JS) on `/`.
2. Proxies API calls matching `/api/tasks` to `http://task-service:8080/api/tasks`.
3. Proxies API calls matching `/api/quotes` to `http://quote-service:8080/api/quotes`.
4. Proxies Prometheus metrics scraping calls (`/actuator/prometheus`).
This prevents Cross-Origin Resource Sharing (CORS) issues in the browser.

### Q54: How does DNS mapping (e.g., DuckDNS) interact with the GCP Static IP?
**Answer:** DNS maps a human-readable hostname (`java-gke-app.duckdns.org`) to an A-Record pointing to `35.232.126.138`. When a browser makes a request to `http://java-gke-app.duckdns.org`, DNS resolves it to `35.232.126.138`. No changes are required in Kubernetes manifests or Helm charts when binding custom DNS domains to static LoadBalancer IPs.

### Q55: How do Kubernetes ClusterIP Services communicate internally?
**Answer:** Kubernetes maintains an internal DNS server (CoreDNS). Services are assigned a cluster-internal domain: `<service-name>.<namespace>.svc.cluster.local`. Nginx proxies requests to `http://task-service:8080`, which CoreDNS resolves to the ClusterIP of `task-service`, and kube-proxy load balances across healthy `task-service` Pod endpoints.

### Q56: Why did `http://35.232.126.138` work while `https://35.232.126.138` failed initially?
**Answer:** The Nginx container was configured to listen exclusively on Port 80 (HTTP). Port 443 (HTTPS) was not configured with an SSL/TLS certificate in Nginx or GCP Ingress. Browsers automatically prefixing `https://` experienced TCP connection refusal on Port 443.

### Q57: What is the difference between Kubernetes `Service` types: ClusterIP, NodePort, LoadBalancer, and Ingress?
**Answer:**
- **ClusterIP:** Exposes service on a cluster-internal IP only (unreachable outside cluster).
- **NodePort:** Exposes service on each Node's IP at a static port (30000-32767).
- **LoadBalancer:** Provisions an external Cloud Provider Load Balancer (e.g., GCP Network Load Balancer) pointing to NodePorts.
- **Ingress:** Layer 7 (HTTP/HTTPS) router supporting path-based routing, SSL termination, and single IP multi-host management.

### Q58: How do Kubernetes `livenessProbe` and `readinessProbe` work in `frontend.yaml`?
**Answer:**
- **Readiness Probe (`tcpSocket: port 80`):** Checks if Nginx is ready to accept traffic. If it fails, Kubernetes removes the Pod from the Service load balancer endpoints.
- **Liveness Probe (`tcpSocket: port 80`):** Checks if Nginx is alive. If it fails repeatedly, Kubernetes kills and restarts the Pod container.

### Q59: How do you configure Nginx to proxy Prometheus metrics for multiple microservices?
**Answer:** In `nginx.conf`:
```nginx
location /actuator/prometheus {
    proxy_pass http://task-service:8080/actuator/prometheus;
}
location /actuator/quote-prometheus {
    proxy_pass http://quote-service:8080/actuator/prometheus;
}
```

### Q60: How do you handle zero-downtime rolling updates for frontend and backend deployments?
**Answer:** Kubernetes Deployments use `RollingUpdate` strategy by default (`maxSurge: 25%`, `maxUnavailable: 25%`). When a new image tag is deployed, Kubernetes spins up new Pods first, waits for `readinessProbe` to pass, and then terminates old Pods gracefully.

---

## Section 7: Microservices, PostgreSQL & Stateful Storage (Q61 – Q70)

### Q61: How is PostgreSQL deployed and configured in the Kubernetes cluster?
**Answer:** PostgreSQL 15 is deployed via a StatefulSet/Deployment manifest ([`postgres.yaml`](file:///C:/Users/AjitP/.gemini/antigravity/scratch/java-gke-cicd/helm/java-app/templates/postgres.yaml)) with a `PersistentVolumeClaim` (`postgres-pvc`) requesting persistent disk storage. Database credentials (`POSTGRES_PASSWORD`) are injected securely via Kubernetes Secrets (`postgres-secrets`).

### Q62: Why did we clean up old PostgreSQL StatefulSets and PVCs in CI/CD step 12?
**Answer:** During pipeline testing, switching between Deployment and StatefulSet definitions for PostgreSQL caused Immutable Field errors (`spec.selector` cannot be mutated). Step 12 executes a force cleanup (`kubectl delete statefulset/pvc`) to ensure clean idempotent Helm upgrades during deployment tests.

### Q63: How does `task-service` establish database connections to PostgreSQL inside GKE?
**Answer:** In `application.properties`:
`spring.datasource.url=jdbc:postgresql://postgres-service:5432/taskdb`
`task-service` uses standard JDBC drivers to connect to Kubernetes ClusterIP Service `postgres-service` on port 5432. Spring Data JPA / Hibernate automatically manages connection pooling (HikariCP) and schema updates (`spring.jpa.hibernate.ddl-auto=update`).

### Q64: How are Spring Boot environment variables overridden in Kubernetes Deployment manifests?
**Answer:** Kubernetes passes environment variables under `env` in container specs:
```yaml
env:
  - name: SPRING_DATASOURCE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secrets
        key: password
```
Spring Boot automatically maps `SPRING_DATASOURCE_PASSWORD` to override `spring.datasource.password` in `application.properties`.

### Q65: What is the difference between a PersistentVolume (PV) and a PersistentVolumeClaim (PVC)?
**Answer:**
- **PV:** The physical storage volume provisioned in GCP (e.g., GCP Persistent Disk).
- **PVC:** A developer's request for storage (requesting 5Gi, ReadWriteOnce). Kubernetes binds the PVC to an available PV automatically using StorageClasses (`standard-rwo`).

### Q66: How do you prevent data loss when deleting Helm releases containing databases?
**Answer:** Set Helm resource annotations or use `helm.sh/resource-policy: keep` on the PVC manifest. This instructs Helm to leave the `PersistentVolumeClaim` intact in the cluster even when `helm uninstall` is executed.

### Q67: How do Spring Boot microservices handle graceful shutdown in Kubernetes?
**Answer:** Enable `server.shutdown=graceful` in `application.properties`. When Kubernetes sends SIGTERM signal to the Pod during termination, Spring Boot stops accepting new HTTP requests and allows active in-flight database transactions to complete before shutting down.

### Q68: How do you run database schema migrations (Liquibase/Flyway) in Kubernetes?
**Answer:** Use a Kubernetes `Job` or `initContainer` that runs Liquibase/Flyway migrations before the main application container starts. This prevents multiple application replicas from running concurrent schema DDL alterations.

### Q69: What is HikariCP and how do you configure connection pool size for microservices?
**Answer:** HikariCP is the high-performance default JDBC connection pool in Spring Boot. Configure pool limits in `application.properties`:
`spring.datasource.hikari.maximum-pool-size=10`
`spring.datasource.hikari.minimum-idle=5`

### Q70: How do you troubleshoot database connection timeout `PSQLException: Connection refused`?
**Answer:**
1. Check if `postgres-service` is running (`kubectl get svc postgres-service`).
2. Verify PostgreSQL Pod status (`kubectl get pods -l app=postgres`).
3. Check PostgreSQL logs (`kubectl logs -l app=postgres`).
4. Exec into `task-service` pod and test port connectivity (`nc -zv postgres-service 5432`).

---

## Section 8: New Relic APM Observability (Q71 – Q80)

### Q71: How does the New Relic Java Agent instrument Spring Boot applications?
**Answer:** The Java Agent relies on **JVM Bytecode Instrumentation** via the Java Attach API / `-javaagent` flag. When Spring Boot classes are loaded into memory, the agent modifies class bytecode on-the-fly, inserting timing and tracing hooks around `@RestController` methods, JDBC SQL queries, and HTTP client calls.

### Q72: How are New Relic credentials and app names injected into GKE Pods?
**Answer:** Passed via Kubernetes container environment variables:
```yaml
env:
  - name: JAVA_TOOL_OPTIONS
    value: "-javaagent:/newrelic/newrelic.jar"
  - name: NEW_RELIC_APP_NAME
    value: "task-service"
  - name: NEW_RELIC_LICENSE_KEY
    valueFrom:
      secretKeyRef:
        name: newrelic-secrets
        key: license-key
```

### Q73: What telemetry data does New Relic APM collect automatically?
**Answer:**
1. Transaction response times and throughput (RPM).
2. Database query execution time and slow query traces.
3. JVM garbage collection (GC) metrics, heap/non-heap memory utilization.
4. Unhandled runtime exceptions and error rates.
5. Distributed tracing headers across microservices.

### Q74: Why did we use New Relic EU Collector endpoint configuration?
**Answer:** New Relic accounts created in the European region require directing agent telemetry to the EU collector backend (`collector.eu01.nr-data.net`). In `newrelic.yml` or via environment variable `NEW_RELIC_HOST=collector.eu01.nr-data.net`, the agent routes data to the EU tenant endpoint over HTTPS Port 443.

### Q75: Does the New Relic Java Agent impact microservice startup performance?
**Answer:** Bytecode transformation adds a minor overhead (~1-2 seconds) during initial JVM class loading at boot time. Once classes are loaded, runtime CPU overhead is negligible (< 1-2%) due to asynchronous telemetry batching.

### Q76: How do you verify New Relic Agent startup in pod logs?
**Answer:** Inspect application stdout/stderr (`kubectl logs <pod-name>`):
```text
Info: Reporting to: https://collector.eu01.nr-data.net:443
Info: Agent is connected to New Relic APM
Info: Real-time telemetry reporting enabled for task-service
```

### Q77: How does New Relic APM track distributed transactions across microservices?
**Answer:** New Relic injects W3C Trace Context headers (`traceparent`, `tracestate`) into outgoing HTTP headers when `task-service` calls `quote-service`. The receiving service agent reads the headers, allowing New Relic to map the entire cross-service call graph in an End-to-End Distributed Trace.

### Q78: How do you mask sensitive data (SSN, Passwords, SQL Parameters) in New Relic APM?
**Answer:** Enable High Security Mode (HSM) or set `record_sql: obfuscated` in agent configuration. This replaces raw SQL parameter values (e.g., `WHERE password = 'xyz'`) with `?` placeholders before transmitting telemetry to the cloud.

### Q79: What is the difference between APM Monitoring and Infrastructure Monitoring?
**Answer:**
- **APM (Application Performance Monitoring):** Focuses inside the JVM code (methods, database queries, exceptions, frameworks).
- **Infrastructure Monitoring:** Focuses outside the container on host/node OS metrics (CPU core utilization, disk I/O, network interface packets).

### Q80: How do you handle New Relic agent updates across multiple microservices?
**Answer:** Centralize the agent JAR in Artifactory (`generic-local/newrelic/newrelic.jar`). Updating the single JAR in Artifactory automatically updates the agent baked into all microservice container images during the next CI/CD build execution.

---

## Section 9: Prometheus & Grafana Observability Architecture (Q81 – Q90)

### Q81: Explain the architecture of using a Standalone VM for Prometheus & Grafana to monitor GKE workloads.
**Answer:** Standalone VM (`137.23.52.82`) runs Prometheus (Port 9090) and Grafana (Port 3000) inside Docker containers. Spring Boot microservices on GKE expose Actuator endpoints (`/actuator/prometheus`). Prometheus on the VM periodically polls (scrapes) the GKE Static IP (`35.232.126.138`) every 15 seconds. Grafana queries Prometheus via PromQL to render visualization dashboards.

### Q82: What dependencies and properties are required to expose Prometheus metrics in Spring Boot 3?
**Answer:**
1. **`build.gradle`**:
   `implementation 'org.springframework.boot:spring-boot-starter-actuator'`
   `implementation 'io.micrometer:micrometer-registry-prometheus'`
2. **`application.properties`**:
   `management.endpoints.web.exposure.include=health,info,prometheus`
   `management.endpoint.prometheus.enabled=true`
   `management.metrics.export.prometheus.enabled=true`

### Q83: How did you configure Nginx reverse proxy to route Prometheus scraping requests to internal pods?
**Answer:** In `frontend/nginx.conf`:
```nginx
location /actuator/prometheus {
    proxy_pass http://task-service:8080/actuator/prometheus;
}
location /actuator/quote-prometheus {
    proxy_pass http://quote-service:8080/actuator/prometheus;
}
```

### Q84: What is the structural difference between Metrics (Prometheus) and Managed Logs (GCP Cloud Logging)?
**Answer:**
- **Metrics (Prometheus):** Numerical time-series data (timestamp + value). Ultra-compact, low storage cost, fast aggregation via PromQL. Answers *"HOW MUCH / WHEN"*.
- **Logs (GCP Logging):** Timestamped text lines (`stdout`/`stderr`). High storage footprint, pay-per-GB ingestion cost, text search. Answers *"WHY / EXACT ERROR STACK TRACE"*.

### Q85: What is PromQL and give an example query for monitoring Spring Boot HTTP error rates.
**Answer:** PromQL (Prometheus Query Language) queries time-series metrics.
Example to calculate 5-minute HTTP 500 error rate:
`sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m])) / sum(rate(http_server_requests_seconds_count[5m])) * 100`

### Q86: What are standard Grafana Dashboard IDs for JVM and Spring Boot monitoring?
**Answer:**
- **Dashboard `11378`**: JVM (Micrometer) Metrics (Heap/Non-Heap memory, GC pauses, Thread states, CPU usage).
- **Dashboard `4701`**: Spring Boot Statistics (HTTP throughput, latency percentiles p95/p99, database pool status).

### Q87: Why is pulling metrics from an external VM cost-effective for GKE Autopilot?
**Answer:** Installing heavy monitoring operators (Prometheus Operator, Grafana, Alertmanager) inside GKE Autopilot consumes Pod CPU/RAM requests billed 24/7 by Google. Running Prometheus/Grafana on a fixed-cost standalone VM reduces GKE resource requests to 0 while keeping historical metrics intact even when GKE workloads are uninstalled.

### Q88: How does Prometheus handle target unavailability if GKE workloads are down?
**Answer:** Prometheus marks the target state as `DOWN` on `http://137.23.52.82:9090/targets` and records `up == 0`. When GKE workloads are re-deployed, Prometheus automatically resumes metric collection on the next 15-second scrape cycle without requiring a container restart.

### Q89: What is Micrometer in the Spring Boot ecosystem?
**Answer:** Micrometer is a vendor-neutral application metrics facade (similar to SLF4J for logging). It allows Spring Boot developers to instrument code once and export metrics to multiple monitoring backends (Prometheus, Datadog, New Relic, InfluxDB) simultaneously.

### Q90: How do you configure alerting rules in Prometheus?
**Answer:** Define alert rules in `alert.rules.yml` on the VM:
```yaml
groups:
  - name: gke_alerts
    rules:
      - alert: TaskServiceDown
        expr: up{job="gke-task-service"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Task Service is unreachable on GKE"
```

---

## Section 10: GitHub Actions CI/CD, PR Workflows & Optimization (Q91 – Q100)

### Q91: How does the PR-driven workflow separate CI verification from CD deployment?
**Answer:** In `.github/workflows/deploy.yml`:
- **PR Event (`pull_request`)**: Triggers **CI Steps** (Checkout, Java 17, `./gradlew test`). Deployment steps are skipped using conditionals (`if: github.event_name == 'push'`).
- **Merge Event (`push` to `main`)**: Triggers **CD Steps** (WIF Auth, Artifactory push, Helm GKE upgrade).

### Q92: How did you fix the GitHub Actions Linux runner error `./gradlew: Permission denied`?
**Answer:** Linux runners require executable file permissions (`+x`) on shell scripts.
1. Updated Git index: `git update-index --chmod=+x task-service/gradlew quote-service/gradlew`.
2. Added defensive workflow step: `chmod +x task-service/gradlew quote-service/gradlew || true`.

### Q93: What is `paths-ignore` in GitHub Actions and why is it critical for pipeline optimization?
**Answer:** `paths-ignore` prevents pipeline execution when specific non-code files are modified:
```yaml
on:
  push:
    branches: [main]
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.gitignore'
```
Editing documentation or markdown files bypasses CI/CD entirely, saving runner minutes and preventing unnecessary builds.

### Q94: How do you pass dynamic container image tags (Git SHA) to Helm during deployment?
**Answer:** Pass current commit SHA (`${{ github.sha }}`) via Helm CLI flags:
```bash
helm upgrade --install java-app ./helm/java-app \
  --set frontend.image.tag=${{ github.sha }} \
  --set taskService.image.tag=${{ github.sha }} \
  --set quoteService.image.tag=${{ github.sha }}
```

### Q95: What is `workflow_dispatch` in GitHub Actions?
**Answer:** `workflow_dispatch` adds a manual **"Run workflow"** button in the GitHub Actions UI. It allows DevOps engineers to trigger builds on demand with custom inputs without pushing new code commits.

### Q96: How do you secure base64 Docker credentials passed into Helm during pipeline execution?
**Answer:** Construct the JSON string in memory, base64 encode it without printing to stdout, and pass it directly to Helm via environment variables:
```bash
DOCKER_CONFIG_JSON=$(echo -n "..." | base64 -w 0)
helm upgrade --install java-app ... --set artifactory.dockerConfigJson="${DOCKER_CONFIG_JSON}"
```

### Q97: What is the purpose of `--wait --timeout 5m` in `helm upgrade --install`?
**Answer:** `--wait` forces Helm to block pipeline execution until all Kubernetes Deployment Pods pass `readinessProbe` and reach `Running` state. If Pods fail or crash within 5 minutes, Helm marks the pipeline step as `FAILED` and exits, preventing broken deployments.

### Q98: How do you rollback a failed Helm release in CI/CD?
**Answer:** Execute `helm rollback java-app <revision-number>`. In GitHub Actions, add a cleanup step using `if: failure()`:
```yaml
- name: Rollback Helm Release on Failure
  if: failure()
  run: helm rollback java-app
```

### Q99: What permissions block is required in GitHub Actions for WIF OIDC authentication?
**Answer:**
```yaml
permissions:
  contents: read
  id-token: write
```
`id-token: write` permits fetching the OIDC JWT assertion, while `contents: read` allows checking out repository source code.

### Q100: Summarize the end-to-end flow of a developer commit from local machine to GKE production.
**Answer:**
1. Developer pushes branch and opens Pull Request -> GitHub Actions runs **CI Unit Tests** (`./gradlew test`).
2. Tech Lead approves and merges PR to `main` -> GitHub Actions triggers **CD Pipeline**.
3. Runner authenticates keylessly with GCP via **WIF (OIDC)**.
4. Runner fetches `newrelic.jar` from **Artifactory `generic-local`**.
5. **Gradle Jib** bakes agent into OCI image layers and pushes to **Artifactory `docker-local`**.
6. **Helm** upgrades GKE release, injecting `artifactory-docker-secret` and Static IP (`35.232.126.138`).
7. GKE Kubelet pulls images over HTTPS and starts Pods.
8. JVM loads New Relic Agent for APM telemetry, while VM Prometheus (`137.23.52.82:9090`) scrapes Actuator metrics every 15s for Grafana (`137.23.52.82:3000`) dashboards.
