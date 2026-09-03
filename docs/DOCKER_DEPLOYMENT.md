# Docker Deployment

### Build Image
```bash
docker build -t fractal-core:latest .
```

### Run Container
```bash
docker run -d --name fractal-app \
  -p 8000:8000 \
  -v $(pwd)/state:/app/state \
  -v $(pwd)/config.yaml:/app/config.yaml \
  fractal-core:latest
```

### Docker Compose
```bash
docker-compose up -d
```
