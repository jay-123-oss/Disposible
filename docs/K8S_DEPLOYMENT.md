# Kubernetes Deployment

### Apply Manifests
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### Check Rollout Status
```bash
kubectl rollout status deployment/fractal-core-deployment
```
