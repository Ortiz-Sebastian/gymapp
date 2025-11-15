# Kubernetes Deployment for GymApp

This directory contains Kubernetes manifests for deploying the GymApp to a Kubernetes cluster.

## Prerequisites

1. Kubernetes cluster (v1.24+)
2. kubectl configured to access your cluster
3. Docker images pushed to a container registry
4. Ingress controller installed (e.g., NGINX Ingress)
5. Storage class configured for PersistentVolumes

## Files Overview

- `namespace.yaml` - Creates the `gymapp` namespace
- `configmap.yaml` - Non-sensitive configuration
- `secrets.yaml` - Sensitive data (passwords, API keys)
- `postgres-pvc.yaml` - Persistent volume for PostgreSQL data
- `media-pvc.yaml` - Persistent volume for media files
- `ml-models-pvc.yaml` - Persistent volume for ML models
- `postgres-deployment.yaml` - PostgreSQL database with PostGIS
- `redis-deployment.yaml` - Redis for Celery broker
- `backend-deployment.yaml` - Django backend application
- `celery-worker-deployment.yaml` - Celery worker for background tasks
- `celery-beat-deployment.yaml` - Celery Beat scheduler
- `frontend-deployment.yaml` - React frontend
- `ingress.yaml` - Ingress for external access
- `kustomization.yaml` - Kustomize configuration (optional)

## Setup Instructions

### 1. Build and Push Docker Images

First, build and push your Docker images to a container registry:

```bash
# Build backend image
cd Backend
docker build -t your-registry/gymapp-backend:latest .
docker push your-registry/gymapp-backend:latest

# Build frontend image
cd ../Frontend
docker build -t your-registry/gymapp-frontend:latest .
docker push your-registry/gymapp-frontend:latest
```

### 2. Update Image References

Replace `your-registry/gymapp-backend:latest` and `your-registry/gymapp-frontend:latest` in:
- `backend-deployment.yaml`
- `celery-worker-deployment.yaml`
- `celery-beat-deployment.yaml`
- `frontend-deployment.yaml`

### 3. Create Secrets

**Option A: Using kubectl (Recommended)**

```bash
kubectl create namespace gymapp

kubectl create secret generic gymapp-secrets \
  --from-literal=SECRET_KEY='your-secret-key-here' \
  --from-literal=POSTGRES_PASSWORD='your-postgres-password' \
  --from-literal=GOOGLE_PLACES_API_KEY='your-api-key' \
  -n gymapp
```

**Option B: Edit secrets.yaml**

Edit `secrets.yaml` with your actual values, then:

```bash
kubectl apply -f secrets.yaml
```

### 4. Update ConfigMap

Edit `configmap.yaml` to match your environment:
- Update `ALLOWED_HOSTS` with your domain
- Update `CORS_ALLOWED_ORIGINS` with your frontend URL

### 5. Update Ingress

Edit `ingress.yaml`:
- Replace `gymapp.example.com` with your actual domain
- Configure TLS certificate (or remove TLS if not using HTTPS)

### 6. Deploy to Kubernetes

**Option A: Apply all files individually**

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f media-pvc.yaml
kubectl apply -f ml-models-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f celery-worker-deployment.yaml
kubectl apply -f celery-beat-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

**Option B: Using the apply script**

```bash
cd k8s
chmod +x apply-all.sh
./apply-all.sh
```

**Option C: Apply all at once**

```bash
kubectl apply -f .
```

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n gymapp

# Check services
kubectl get svc -n gymapp

# Check ingress
kubectl get ingress -n gymapp

# View logs
kubectl logs -f deployment/gymapp-backend -n gymapp
kubectl logs -f deployment/gymapp-celery-worker -n gymapp
kubectl logs -f deployment/gymapp-celery-beat -n gymapp
```

## Scaling

Scale deployments as needed:

```bash
# Scale backend
kubectl scale deployment gymapp-backend --replicas=3 -n gymapp

# Scale Celery workers
kubectl scale deployment gymapp-celery-worker --replicas=4 -n gymapp
```

## Updating

To update your application:

1. Build and push new images
2. Update image tags in deployment files (or use `:latest` if auto-updating)
3. Apply changes:
   ```bash
   kubectl apply -f backend-deployment.yaml
   kubectl rollout status deployment/gymapp-backend -n gymapp
   ```

## Troubleshooting

### Check pod status
```bash
kubectl describe pod <pod-name> -n gymapp
```

### View pod logs
```bash
kubectl logs <pod-name> -n gymapp
```

### Check persistent volumes
```bash
kubectl get pvc -n gymapp
kubectl describe pvc <pvc-name> -n gymapp
```

### Port forward for debugging
```bash
# Backend
kubectl port-forward svc/gymapp-backend 8000:8000 -n gymapp

# Database
kubectl port-forward svc/gymapp-db 5432:5432 -n gymapp
```

## Important Notes

1. **Celery Beat**: Only one replica should run (already configured)
2. **Database**: Consider using a managed PostgreSQL service in production
3. **Storage**: Adjust PVC sizes and storage classes based on your needs
4. **Secrets**: Never commit secrets.yaml with real values to git
5. **Resources**: Adjust CPU/memory limits based on your cluster capacity
6. **Health Checks**: All services have liveness and readiness probes configured

## Production Considerations

- Use managed database service (AWS RDS, Google Cloud SQL, etc.)
- Use managed Redis service (AWS ElastiCache, Google Memorystore, etc.)
- Set up proper monitoring and logging
- Configure resource quotas and limits
- Use Horizontal Pod Autoscaler (HPA) for auto-scaling
- Set up backup strategies for persistent volumes
- Configure network policies for security
- Use cert-manager for automatic TLS certificate management

