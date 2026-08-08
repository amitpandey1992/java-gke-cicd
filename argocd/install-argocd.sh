#!/usr/bin/env bash
set -eo pipefail

PROJECT_ID="project-616fef18-15b8-4d6c-8a2"
REGION="us-central1"
CLUSTER_NAME="java-gke-cluster"
ARGOCD_NAMESPACE="argocd"
TARGET_NAMESPACE="java-app-gitops"

echo "=== [1/5] Authenticating with GKE Autopilot Cluster ==="
gcloud container clusters get-credentials "${CLUSTER_NAME}" --region "${REGION}" --project "${PROJECT_ID}"

echo "=== [2/5] Creating Namespaces (${ARGOCD_NAMESPACE}, ${TARGET_NAMESPACE}) ==="
kubectl apply -f argocd/namespace.yaml

echo "=== [3/5] Installing ArgoCD Controller on GKE Autopilot ==="
kubectl apply -n "${ARGOCD_NAMESPACE}" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "=== [4/5] Waiting for ArgoCD Server to be Ready ==="
kubectl rollout status deployment/argocd-server -n "${ARGOCD_NAMESPACE}" --timeout=300s

echo "=== [5/5] Deploying ArgoCD Application Manifest ==="
kubectl apply -f argocd/application.yaml

echo "=========================================================="
echo "ArgoCD GitOps Setup Complete!"
echo "Retrieving initial admin password..."
echo "=========================================================="
ARGOCD_PASSWORD=$(kubectl -n "${ARGOCD_NAMESPACE}" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode)
echo "Username: admin"
echo "Password: ${ARGOCD_PASSWORD}"
echo "To access ArgoCD UI, run:"
echo "kubectl port-forward svc/argocd-server -n ${ARGOCD_NAMESPACE} 8080:443"
echo "Then visit: https://localhost:8080"
echo "=========================================================="
