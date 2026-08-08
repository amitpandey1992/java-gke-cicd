# PowerShell Script to Install ArgoCD GitOps on GKE Autopilot
$ErrorActionPreference = "Stop"

$ProjectId = "project-616fef18-15b8-4d6c-8a2"
$Region = "us-central1"
$ClusterName = "java-gke-cluster"
$ArgoNamespace = "argocd"
$TargetNamespace = "java-app-gitops"

Write-Host "=== [1/5] Connecting to GKE Autopilot Cluster ===" -ForegroundColor Green
gcloud container clusters get-credentials $ClusterName --region $Region --project $ProjectId

Write-Host "=== [2/5] Creating Namespaces ($ArgoNamespace, $TargetNamespace) ===" -ForegroundColor Green
kubectl apply -f argocd/namespace.yaml

Write-Host "=== [3/5] Deploying ArgoCD Engine to GKE Autopilot ===" -ForegroundColor Green
kubectl apply -n $ArgoNamespace -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

Write-Host "=== [4/5] Awaiting ArgoCD Server Readiness ===" -ForegroundColor Green
kubectl rollout status deployment/argocd-server -n $ArgoNamespace --timeout=300s

Write-Host "=== [5/5] Submitting ArgoCD Application CRD ===" -ForegroundColor Green
kubectl apply -f argocd/application.yaml

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "ArgoCD GitOps Deployment Completed Successfully!" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$EncodedPass = kubectl -n $ArgoNamespace get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
if ($EncodedPass) {
    $DecodedPass = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($EncodedPass))
    Write-Host "ArgoCD UI Username: admin" -ForegroundColor Yellow
    Write-Host "ArgoCD UI Password: $DecodedPass" -ForegroundColor Yellow
}

Write-Host "`nTo access ArgoCD UI locally:" -ForegroundColor Green
Write-Host "kubectl port-forward svc/argocd-server -n $ArgoNamespace 8080:443" -ForegroundColor White
Write-Host "Navigate to: https://localhost:8080" -ForegroundColor White
