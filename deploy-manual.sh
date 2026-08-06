#!/bin/bash
# Exit immediately if any command fails
set -e

echo "============================================"
echo "🚀 Starting Manual Deploy to GKE from Cloud Shell"
echo "============================================"

# Configs
PROJECT_ID="project-616fef18-15b8-4d6c-8a2"
REGION="us-central1"
CLUSTER_NAME="java-gke-cluster"
ARTIFACT_REPO="java-app-repo"

# Ensure License Key is set
if [ -z "$NR_LICENSE_KEY" ]; then
  read -sp "🔑 Enter your New Relic Ingest License Key: " NR_LICENSE_KEY
  echo ""
fi

if [ -z "$NR_LICENSE_KEY" ]; then
  echo "❌ Error: NR_LICENSE_KEY variable is required."
  exit 1
fi

echo "Connecting to GKE Cluster..."
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

echo "Configuring Docker Credentials for Artifact Registry..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo "--------------------------------------------"
echo "📦 1/3: Building and Pushing Frontend Image..."
echo "--------------------------------------------"
cd frontend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/frontend:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/frontend:latest
cd ..

echo "--------------------------------------------"
echo "📦 2/3: Building and Pushing Task Service (Jib)..."
echo "--------------------------------------------"
cd task-service
chmod +x gradlew
./gradlew jib -Djib.to.image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/task-service:latest
cd ..

echo "--------------------------------------------"
echo "📦 3/3: Building and Pushing Quote Service (Jib)..."
echo "--------------------------------------------"
cd quote-service
chmod +x gradlew
./gradlew jib -Djib.to.image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/quote-service:latest
cd ..

echo "--------------------------------------------"
echo "⛵ 4/4: Deploying Microservices App via Helm..."
echo "--------------------------------------------"
helm upgrade --install java-app ./helm/java-app \
  --set frontend.image.repository="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/frontend" \
  --set frontend.image.tag="latest" \
  --set taskService.image.repository="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/task-service" \
  --set taskService.image.tag="latest" \
  --set quoteService.image.repository="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/quote-service" \
  --set quoteService.image.tag="latest" \
  --set newrelic.licenseKey="$NR_LICENSE_KEY" \
  --wait --timeout 5m

echo "--------------------------------------------"
echo "📊 5/5: Deploying New Relic Monitoring Bundle..."
echo "--------------------------------------------"
helm repo add newrelic https://helm-charts.newrelic.com
helm repo update
helm upgrade --install newrelic-bundle newrelic/nri-bundle \
  --namespace newrelic --create-namespace \
  --set global.licenseKey="$NR_LICENSE_KEY" \
  --set global.cluster="$CLUSTER_NAME" \
  --set global.region="EU" \
  --set newrelic-infrastructure.enabled=true \
  --set kube-state-metrics.enabled=true \
  --set pixiesizing.enabled=false

echo "============================================"
echo "✅ Manual Deployment Completed Successfully!"
echo "============================================"
