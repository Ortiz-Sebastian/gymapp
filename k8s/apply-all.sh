#!/bin/bash

# Script to apply all Kubernetes manifests in the correct order

set -e

echo "🚀 Deploying GymApp to Kubernetes..."
echo ""

# Apply in order
echo "1️⃣  Creating namespace..."
kubectl apply -f namespace.yaml

echo "2️⃣  Creating ConfigMap..."
kubectl apply -f configmap.yaml

echo "3️⃣  Creating Secrets..."
kubectl apply -f secrets.yaml

echo "4️⃣  Creating PersistentVolumeClaims..."
kubectl apply -f postgres-pvc.yaml
kubectl apply -f media-pvc.yaml
kubectl apply -f ml-models-pvc.yaml

echo "5️⃣  Deploying PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

echo "6️⃣  Deploying Redis..."
kubectl apply -f redis-deployment.yaml

echo "7️⃣  Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=gymapp-db -n gymapp --timeout=120s || true

echo "8️⃣  Deploying Backend..."
kubectl apply -f backend-deployment.yaml

echo "9️⃣  Deploying Celery Worker..."
kubectl apply -f celery-worker-deployment.yaml

echo "🔟 Deploying Celery Beat..."
kubectl apply -f celery-beat-deployment.yaml

echo "1️⃣1️⃣ Deploying Frontend..."
kubectl apply -f frontend-deployment.yaml

echo "1️⃣2️⃣ Deploying Ingress..."
kubectl apply -f ingress.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status with:"
echo "  kubectl get pods -n gymapp"
echo "  kubectl get svc -n gymapp"
echo "  kubectl get ingress -n gymapp"

