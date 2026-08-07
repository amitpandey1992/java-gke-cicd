# Java Microservices GKE CI/CD Pipeline

Production-ready cloud-native Java microservices application deployed on **Google Kubernetes Engine (GKE Autopilot)** with **JFrog Artifactory**, **New Relic APM**, **Static IP Reservation**, and **GitHub Actions PR-driven CI/CD**.

---

## 🚀 Live Application Endpoint

* **Public Web Application:** [`http://java-gke-app.duckdns.org`](http://java-gke-app.duckdns.org)
* **Direct Static IP:** [`http://35.232.126.138/`](http://35.232.126.138/)
* **Self-Hosted Artifactory:** [`https://my-jfrog-artifactory.duckdns.org/`](https://my-jfrog-artifactory.duckdns.org/)

---

## 🛠️ Architecture Stack

* **Frontend:** Nginx Reverse Proxy serving Single-Page UI.
* **Microservices:** Spring Boot 3.2.2 + Java 17 (`task-service` & `quote-service`).
* **Database:** PostgreSQL 15 with Kubernetes Persistent Volume Claim.
* **Containers:** OCI images compiled via **Gradle Jib** (zero Docker daemon needed).
* **Observability:** **New Relic APM** Java Agent pre-baked into container image layers.
* **CI/CD:** GitHub Actions with **Workload Identity Federation (WIF)** and PR-driven verification.

---

## 📚 Detailed Documentation

All architectural guides, troubleshooting playbooks, and sitemaps are in the [`docs/`](./docs) directory:
* [`docs/master_architecture_guide.md`](./docs/master_architecture_guide.md): Master system sitemap and 12-tool matrix.
* [`docs/dns_sitemap_registry.md`](./docs/dns_sitemap_registry.md): Permanent endpoint registry.
* [`docs/static_ip_architecture_guide.md`](./docs/static_ip_architecture_guide.md): Static IP binding mechanics.
* [`docs/artifactory_troubleshooting_guide.md`](./docs/artifactory_troubleshooting_guide.md): HTTPS SSL migration & Kubelet secrets.
* [`docs/newrelic_setup_guide.md`](./docs/newrelic_setup_guide.md): Java Agent bytecode instrumentation guide.
