# Cloud Deployment

### AWS (ECS / EKS)
Deploy container to AWS ECR and run on Fargate task definition with 4 vCPU / 8 GB RAM.

### Google Cloud (Cloud Run / GKE)
```bash
gcloud run deploy fractal-service \
  --image gcr.io/PROJECT_ID/fractal-core:latest \
  --memory 8Gi --cpu 4
```

### Azure (Container Instances)
Deploy using Azure CLI pointing to Azure Container Registry (ACR).
